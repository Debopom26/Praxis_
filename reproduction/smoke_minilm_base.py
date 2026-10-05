from local_runtime import *
import datetime,time
start=datetime.datetime.now(datetime.timezone.utc).isoformat();t=time.perf_counter()
try:
 import torch
 from transformers import AutoTokenizer,AutoModel
 tokenizer=AutoTokenizer.from_pretrained(str(path("minilm_base")),local_files_only=True)
 model=AutoModel.from_pretrained(str(path("minilm_base")),local_files_only=True).eval()
 inputs=tokenizer("Please verify the caller before sharing credentials.",return_tensors="pt")
 with torch.inference_mode(): output=model(**inputs).last_hidden_state
 assert output.shape[-1]==384 and torch.isfinite(output).all()
 result={"status":"BASE_AVAILABLE_HEAD_MISSING","hidden_size":384,"classifier_outputs_tested":False,"missing":["BEST_MODEL.pt","training_config.json","thresholds.json"]}
except Exception as exc:result={"status":"ERROR","error":str(exc),"type":type(exc).__name__}
report={"started_at":start,"finished_at":datetime.datetime.now(datetime.timezone.utc).isoformat(),"latency_ms":(time.perf_counter()-t)*1000,"worker_id":str(os.getpid()),**result}
(ROOT/"docs/import-2026-09-29/minilm-smoke.json").write_text(json.dumps(report,indent=2),encoding="utf-8");print(json.dumps(report,indent=2))
