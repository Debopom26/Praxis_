from pathlib import Path
import urllib.request,hashlib,zipfile
root=Path(__file__).resolve().parents[2]
archive=root/'.tools/gradle-9.3.1-bin.zip'
if not archive.exists():
 with urllib.request.urlopen('https://downloads.gradle.org/distributions/gradle-9.3.1-bin.zip',timeout=120) as response,archive.open('wb') as f:
  while block:=response.read(1024*1024):f.write(block)
assert hashlib.sha256(archive.read_bytes()).hexdigest()=='b266d5ff6b90eada6dc3b20cb090e3731302e553a27c5d3e4df1f0d76beaff06'
with zipfile.ZipFile(archive) as z:
 for i in z.infolist():
  if i.is_dir():continue
  dest=(root/'.tools'/i.filename).resolve()
  assert dest.is_relative_to((root/'.tools/gradle-9.3.1').resolve())
  if not dest.exists():dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(z.read(i))
print('Verified Gradle 9.3.1 installed')
