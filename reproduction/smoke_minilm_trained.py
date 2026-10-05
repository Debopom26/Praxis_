from local_runtime import *
import datetime,time,numpy as np
from minilm_local import PraxisMiniLMInference
start=datetime.datetime.now(datetime.timezone.utc).isoformat();t=time.perf_counter()
try:
 artifact=path("minilm_trained"); config=json.loads((artifact/"training_config.json").read_text())
 assert config["labels"]==CONFIG["locked_labels"]
 assert config["revision"]==CONFIG["models"]["minilm_base"]["revision"]
 detector=PraxisMiniLMInference(artifact,device="cpu",local_model_path=path("minilm_base"))
 saved=json.loads((path("imported_runtime")/"PRAXIS_FINAL_ALL_MODELS_RESULT.json").read_text())
 result=detector.analyze(saved["transcript"])
 assert list(result["probabilities"])==CONFIG["locked_labels"]
 assert len(result["probabilities"])==8 and np.isfinite(list(result["probabilities"].values())).all()
 diffs={k:result["probabilities"][k]-saved["evidence"]["minilm"]["probabilities"][k] for k in CONFIG["locked_labels"]}
 report={"status":"AVAILABLE","outputs":8,"locked_label_order_verified":True,"strict_state_load":True,"checkpoint_epoch":detector.checkpoint_epoch,"result":result,"probability_deltas_vs_saved":diffs}
except Exception as exc:report={"status":"ERROR","error":str(exc),"type":type(exc).__name__}
report.update(started_at=start,finished_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),latency_ms=(time.perf_counter()-t)*1000,worker_id=str(os.getpid()))
(ROOT/"docs/import-2026-09-29/minilm-trained-smoke.json").write_text(json.dumps(report,indent=2),encoding="utf-8");print(json.dumps(report,indent=2))
