"""Resumable official-wheel transfer, disjoint ranges, final publisher SHA-256 verification."""
import concurrent.futures,hashlib,json,re,threading,time,urllib.request,urllib.parse
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
name="torch-2.1.2+cu121-cp310-cp310-linux_x86_64.whl"
target=ROOT/".cache/wheels"/name
state_file=ROOT/".cache/wheels/torch-download-state.json"
index=urllib.request.urlopen("https://download.pytorch.org/whl/cu121/torch/",timeout=60).read().decode()
links=re.findall(r'href="([^"]+)"',index)
link=next(x for x in links if urllib.parse.unquote(x.split("#")[0]).endswith("/"+name))
url,expected=link.split("#sha256=")
url="https://download.pytorch.org/whl/cu121/torch-2.1.2%2Bcu121-cp310-cp310-linux_x86_64.whl"
size=2200673027
if state_file.exists():state=json.loads(state_file.read_text())
else:
 prefix=target.stat().st_size if target.exists() else 0
 state={"prefix":prefix,"done":[],"size":size,"sha256":expected}
 state_file.write_text(json.dumps(state))
 with target.open("r+b" if target.exists() else "wb") as f:f.truncate(size)
lock=threading.Lock(); step=8*1024*1024
ranges=[(s,min(size-1,s+step-1)) for s in range(state["prefix"],size,step) if s not in state["done"]]
def download(bounds):
 start,end=bounds
 for attempt in range(5):
  try:
   req=urllib.request.Request(url,headers={"Range":f"bytes={start}-{end}"})
   with urllib.request.urlopen(req,timeout=90) as response:
    if response.status!=206 or response.headers.get("Content-Range")!=f"bytes {start}-{end}/{size}":raise RuntimeError("Unexpected range response")
    data=response.read()
   if len(data)!=end-start+1:raise RuntimeError("Incomplete range")
   with target.open("r+b") as f:f.seek(start);f.write(data)
   with lock:
    state["done"].append(start);state_file.write_text(json.dumps(state))
    if len(state["done"])%8==0:print("Completed ranges",len(state["done"]),flush=True)
   return
  except Exception:
   if attempt==4:raise
   time.sleep(2)
with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:list(pool.map(download,ranges))
h=hashlib.sha256()
with target.open("rb") as f:
 while b:=f.read(8*1024*1024):h.update(b)
if h.hexdigest()!=expected:raise RuntimeError("Publisher hash mismatch")
(ROOT/"docs/import-2026-09-29/torch-wheel-verified.json").write_text(json.dumps({"file":name,"bytes":size,"sha256":expected,"publisher_sha256_verified":True},indent=2))
print("Publisher SHA-256 verified",expected,flush=True)
