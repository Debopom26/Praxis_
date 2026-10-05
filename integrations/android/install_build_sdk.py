import urllib.request,xml.etree.ElementTree as E,zipfile,hashlib
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
root=Path(__file__).resolve().parents[2]
sdk=root/'.tools/android-sdk'
r=E.fromstring(urllib.request.urlopen('https://dl.google.com/android/repository/repository2-3.xml',timeout=30).read())
jobs=[]
for p in r.findall('remotePackage'):
 if p.get('path') in ['platforms;android-37.0','build-tools;37.0.0']:
  license_id=p.find('uses-license').get('ref')
  assert (sdk/'licenses'/license_id).exists(), 'Unaccepted SDK license'
  a=next(a for a in p.findall('archives/archive') if a.findtext('host-os') in [None,'windows'])
  jobs.append((p.get('path'),a.findtext('complete/url'),a.findtext('complete/checksum')))
def install(job):
 name,url,checksum=job
 archive=root/'.tools'/url
 if not archive.exists():
  with urllib.request.urlopen('https://dl.google.com/android/repository/'+url,timeout=120) as response,archive.open('wb') as f:
   while block:=response.read(1024*1024):f.write(block)
 assert hashlib.sha1(archive.read_bytes()).hexdigest()==checksum
 dest=sdk/('platforms/android-37.0' if name.startswith('platforms') else 'build-tools/37.0.0')
 if dest.exists():return
 with zipfile.ZipFile(archive) as z:
  files=[i for i in z.infolist() if not i.is_dir()]
  prefix=files[0].filename.split('/')[0]+'/'
  for i in files:
   assert i.filename.startswith(prefix)
   path=(dest/i.filename[len(prefix):]).resolve()
   assert path.is_relative_to(dest.resolve())
   path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(z.read(i))
 print('Installed',name,flush=True)
with ThreadPoolExecutor(max_workers=2) as pool:list(pool.map(install,jobs))
