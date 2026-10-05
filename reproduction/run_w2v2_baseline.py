from local_runtime import *
import io,subprocess,numpy as np
windows=np.stack(baseline_windows(decode_baseline_audio()))
assert windows.shape==(54,64000)
buffer=io.BytesIO();np.save(buffer,windows,allow_pickle=False)
command=["wsl","-d","Ubuntu-24.04","--","sh","-lc","cd /mnt/c/Users/KIIT/Downloads/Praxis_ && /home/kiit/.local/share/praxis/w2v2-py310/bin/python -u -B reproduction/w2v2_worker_local.py"]
with (ROOT/"docs/import-2026-09-29/w2v2-inference.log").open("w",encoding="utf-8") as log:
 process=subprocess.Popen(command,stdin=subprocess.PIPE,stdout=log,stderr=subprocess.STDOUT)
 process.communicate(buffer.getvalue())
 if process.returncode:raise RuntimeError(f"W2V2 worker failed: {process.returncode}; inspect w2v2-inference.log")
report=json.loads((ROOT/"docs/import-2026-09-29/w2v2-local-results.json").read_text())
valid=[x for x in report["results"] if x.get("available")]
if len(valid)!=54:raise RuntimeError(f"Only {len(valid)}/54 windows succeeded")
peak=max(valid,key=lambda x:x["spoof_softmax"])
summary={"valid_windows":len(valid),"peak_spoof_probability":peak["spoof_softmax"],"prediction":peak["predicted_class"],"peak_window_index":peak["window_index"],"recorded_probability":0.9998408555984497,"absolute_delta":abs(peak["spoof_softmax"]-0.9998408555984497)}
(ROOT/"docs/import-2026-09-29/w2v2-baseline-summary.json").write_text(json.dumps(summary,indent=2),encoding="utf-8");print(json.dumps(summary))
