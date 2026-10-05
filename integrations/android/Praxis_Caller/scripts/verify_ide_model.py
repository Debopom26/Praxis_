"""Inspect real AGP IDE models. This does not open Android Studio."""
import argparse, os, pathlib, subprocess, sys

root = pathlib.Path(__file__).resolve().parents[1]
p = argparse.ArgumentParser()
for name in ('java-home', 'android-sdk', 'gradle-home', 'work-dir'):
    p.add_argument('--' + name, type=pathlib.Path, required=True)
args = p.parse_args()
work = args.work_dir.resolve()
classes = work / 'model-check'
classes.mkdir(parents=True, exist_ok=True)
models = list((work / 'gradle-home/caches/modules-2/files-2.1/com.android.tools.build/builder-model/9.1.1').glob('*/*.jar'))
if len(models) != 1:
    raise RuntimeError('Run the app build first to resolve exactly one AGP 9.1.1 builder-model jar')
cp = os.pathsep.join([str(args.gradle_home.resolve() / 'lib/*'), str(models[0])])
log = root / 'evidence/phase1/ide-model.log'
with log.open('w') as out:
    subprocess.run([str(args.java_home.resolve() / 'bin/javac.exe'), '-cp', cp, '-d', str(classes),
                    str(root / 'scripts/CheckAndroidModel.java')], stdout=out, stderr=subprocess.STDOUT, check=True)
    result = subprocess.run([str(args.java_home.resolve() / 'bin/java.exe'), '-cp', str(classes) + os.pathsep + cp,
                             'CheckAndroidModel', str(root), str(args.gradle_home.resolve()), str(args.java_home.resolve()),
                             str(work), str(args.android_sdk.resolve())], stdout=out, stderr=subprocess.STDOUT)
print(log.read_text())
sys.exit(result.returncode)
