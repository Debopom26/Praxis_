from local_runtime import *
import datetime,time,numpy as np
from adapters.prosody_feature_adapter import PraxisProsodyFeatureAdapter
start=datetime.datetime.now(datetime.timezone.utc).isoformat(); t=time.perf_counter()
audio=decode_audio()
result=PraxisProsodyFeatureAdapter(path("prosody")).analyze(audio)
result.pop("features",None)
report={"started_at":start,"finished_at":datetime.datetime.now(datetime.timezone.utc).isoformat(),"latency_ms":(time.perf_counter()-t)*1000,"worker_id":str(os.getpid()),"status":result["status"],"audio_samples":len(audio),"duration_s":len(audio)/16000,"full_windows_4s_hop2s":len(range(0,len(audio)-64000+1,32000)),"decoder":"PyAV 16.1.0 mono 16kHz; original preprocessing source absent","prosody":result}
(ROOT/"docs/import-2026-09-29/audio-prosody-smoke.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
print(json.dumps(report,indent=2))
