"""Run a clean standalone SDK build/test/lint with workspace-local tool state."""
import argparse, datetime, json, os, pathlib, re, shutil, subprocess, sys

root = pathlib.Path(__file__).resolve().parents[1]
p = argparse.ArgumentParser()
p.add_argument('--java-home', required=True, type=pathlib.Path)
p.add_argument('--android-sdk', required=True, type=pathlib.Path)
p.add_argument('--gradle-home', type=pathlib.Path)
p.add_argument('--work-dir', type=pathlib.Path, default=root/'.local')
p.add_argument('--run-name', default='sdk-verification')
p.add_argument('--runtime', action='store_true', help='Verify the explicit sdk-runtime safety derivative')
args = p.parse_args()
project = root / ('sdk-runtime' if args.runtime else 'sdk')
assert re.fullmatch(r'[a-zA-Z0-9_-]+', args.run_name)
env = os.environ.copy()
env.update(JAVA_HOME=str(args.java_home.resolve()), ANDROID_HOME=str(args.android_sdk.resolve()),
           ANDROID_USER_HOME=str(args.work_dir.resolve()/'android-user'),
           GRADLE_USER_HOME=str(args.work_dir.resolve()/'gradle-home'))
for key in ('ANDROID_USER_HOME','GRADLE_USER_HOME'): pathlib.Path(env[key]).mkdir(parents=True,exist_ok=True)
gradle = args.gradle_home.resolve()/'bin/gradle.bat' if args.gradle_home else root/'sdk/gradlew.bat'
command = [str(gradle), '-p', str(project), '--no-daemon', '--console=plain', '--no-build-cache',
           '-Pkotlin.compiler.execution.strategy=in-process', '-Pkotlin.incremental=false',
           'clean', ':praxis:assembleRelease', ':praxis:testDebugUnitTest', ':praxis:lintRelease']
evidence=root/'evidence'
meta=dict(startedUtc=datetime.datetime.now(datetime.timezone.utc).isoformat(),command=command,
          javaHome=env['JAVA_HOME'],androidSdk=env['ANDROID_HOME'],workDir=str(args.work_dir.resolve()))
with (evidence/f'{args.run_name}-java.txt').open('w') as f:
    subprocess.run([str(args.java_home.resolve()/'bin/java.exe'),'-version'],env=env,stdout=f,stderr=subprocess.STDOUT,check=True)
with (evidence/f'{args.run_name}.log').open('w') as f:
    result=subprocess.run(command,env=env,stdout=f,stderr=subprocess.STDOUT)
meta.update(finishedUtc=datetime.datetime.now(datetime.timezone.utc).isoformat(),exitCode=result.returncode)
(evidence/f'{args.run_name}.json').write_text(json.dumps(meta,indent=2))
reports=evidence/f'{args.run_name}-reports'
reports.mkdir(exist_ok=True)
for name in ('test-results/testDebugUnitTest/TEST-io.praxis.sdk.ContractTest.xml',
             'reports/lint-results-release.txt','reports/lint-results-release.xml'):
    source=project/'praxis/build'/name
    if source.exists(): shutil.copy2(source,reports/source.name)
for source in (project/'praxis/build/test-results/testDebugUnitTest').glob('TEST-*.xml'):
    shutil.copy2(source, reports/source.name)
print(f'Exit {result.returncode}; log: {evidence / (args.run_name + ".log")}',flush=True)
sys.exit(result.returncode)
