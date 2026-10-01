"""Phase 1 app checks. Uses explicit workspace tools; records failures and reports."""
import argparse,datetime,json,os,pathlib,re,shutil,subprocess,sys
root=pathlib.Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser()
p.add_argument('--java-home',type=pathlib.Path,required=True)
p.add_argument('--android-sdk',type=pathlib.Path,required=True)
p.add_argument('--gradle-home',type=pathlib.Path)
p.add_argument('--work-dir',type=pathlib.Path,default=root/'.local')
p.add_argument('--run-name',default='app-check')
p.add_argument('--phase',type=int,default=1,choices=range(1,11))
p.add_argument('--bootstrap-wrapper',action='store_true')
args=p.parse_args()
if (root/'gradle/gradle-daemon-jvm.properties').exists():
 raise RuntimeError('Daemon JVM criteria override JAVA_HOME. Remove the generated override before verifying the required JDK17 toolchain.')
assert re.fullmatch('[a-zA-Z0-9_-]+',args.run_name)
env=os.environ.copy()
env.update(JAVA_HOME=str(args.java_home.resolve()),ANDROID_HOME=str(args.android_sdk.resolve()),
 ANDROID_USER_HOME=str(args.work_dir.resolve()/'android-user'),GRADLE_USER_HOME=str(args.work_dir.resolve()/'gradle-home'))
for key in ('ANDROID_USER_HOME','GRADLE_USER_HOME'): pathlib.Path(env[key]).mkdir(parents=True,exist_ok=True)
(root/'.local').mkdir(exist_ok=True)
(root/'.local/test-home').mkdir(exist_ok=True)
gradle=args.gradle_home.resolve()/'bin/gradle.bat' if args.gradle_home else root/'gradlew.bat'
command=[str(gradle),'-p',str(root),'--no-daemon','--console=plain','--no-build-cache']
if args.bootstrap_wrapper:
 command+=['wrapper','--gradle-version','9.3.1','--distribution-type','bin','--gradle-distribution-sha256-sum',
           'b266d5ff6b90eada6dc3b20cb090e3731302e553a27c5d3e4df1f0d76beaff06','--network-timeout','60000','--no-validate-url']
runtime_check=root/'.local/verify-runtime.gradle'
runtime_check.parent.mkdir(exist_ok=True)
runtime_check.write_text('''
gradle.settingsEvaluated {
    println("PRAXIS_DAEMON_JAVA=" + System.getProperty("java.version"))
    println("PRAXIS_DAEMON_JAVA_HOME=" + System.getProperty("java.home"))
    if (JavaVersion.current() != JavaVersion.VERSION_17) {
        throw new GradleException("Praxis verification requires a JDK 17 daemon")
    }
}
allprojects {
    tasks.withType(org.gradle.api.tasks.testing.Test).configureEach {
        doFirst {
            if (javaLauncher.get().metadata.languageVersion.asInt() != 17) {
                throw new GradleException("Praxis tests require JDK 17")
            }
        }
    }
}
''', encoding='utf-8')
command+=['--init-script',str(runtime_check),'clean','assembleDebug','test','lintDebug']
evidence=root/f'evidence/phase{args.phase}'
evidence.mkdir(exist_ok=True)
metadata=dict(startedUtc=datetime.datetime.now(datetime.timezone.utc).isoformat(),command=command,
 javaHome=env['JAVA_HOME'],androidSdk=env['ANDROID_HOME'],workDir=str(args.work_dir.resolve()))
with (evidence/(args.run_name+'-java.txt')).open('w') as f:
 subprocess.run([str(args.java_home.resolve()/'bin/java.exe'),'-version'],env=env,stdout=f,stderr=subprocess.STDOUT,check=True)
with (evidence/(args.run_name+'.log')).open('w') as f:
 result=subprocess.run(command,env=env,stdout=f,stderr=subprocess.STDOUT)
metadata.update(exitCode=result.returncode,finishedUtc=datetime.datetime.now(datetime.timezone.utc).isoformat())
(evidence/(args.run_name+'.json')).write_text(json.dumps(metadata,indent=2))
reports=evidence/(args.run_name+'-reports')
reports.mkdir(exist_ok=True)
build=root/'app/build'
for part in ['test-results/testDebugUnitTest','test-results/testReleaseUnitTest']:
 for source in (build/part).glob('TEST-*.xml'):
  target=reports/pathlib.Path(part).name/source.name
  target.parent.mkdir(exist_ok=True); shutil.copy2(source,target)
for name in ['lint-results-debug.txt','lint-results-debug.xml']:
 source=build/'reports'/name
 if source.exists(): shutil.copy2(source,reports/name)
print(json.dumps(metadata,indent=2),flush=True)
sys.exit(result.returncode)
