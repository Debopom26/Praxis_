"""Persistent baseline worker. Input PCM remains in memory, received through stdin."""
import os,sys,json,time,datetime,io
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.dont_write_bytecode=True
sys.path.insert(0,str(ROOT/"reproduction/w2v2_runtime"))
from adapters.w2v2_adapter import W2V2AASISTAdapter
cfg=json.loads((ROOT/"model_paths.json").read_text())
def asset(key): return str(ROOT/cfg["models"][key]["path"])
paths={"checkpoint":asset("w2v2_checkpoint"),"xlsr_checkpoint":asset("xlsr_fairseq0122"),"repo":asset("w2v2_source")}
windows=np.load(io.BytesIO(sys.stdin.buffer.read()),allow_pickle=False)
start=datetime.datetime.now(datetime.timezone.utc).isoformat();t=time.perf_counter()
adapter=W2V2AASISTAdapter(paths,device="cpu")
adapter.load()
results=[]
for i,window in enumerate(windows):
 s=datetime.datetime.now(datetime.timezone.utc).isoformat();tick=time.perf_counter()
 r=adapter.analyze(window)
 r.update(window_index=i,started_at=s,finished_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),latency_ms=(time.perf_counter()-tick)*1000,worker_id=str(os.getpid()))
 results.append(r)
 print(f"Window {i+1}/{len(windows)} available={r.get('available')} spoof={r.get('spoof_softmax')}",flush=True)
 report={"started_at":start,"finished_at":datetime.datetime.now(datetime.timezone.utc).isoformat(),"latency_ms":(time.perf_counter()-t)*1000,"worker_id":str(os.getpid()),"status":"RUNNING" if i+1<len(windows) else ("PASS" if all(x.get("available") for x in results) else "FAILED"),"results":results}
 (ROOT/"docs/import-2026-09-29/w2v2-local-results.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
