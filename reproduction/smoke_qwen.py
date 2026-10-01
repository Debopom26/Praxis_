from local_runtime import *
import importlib.util,datetime,time
start=datetime.datetime.now(datetime.timezone.utc).isoformat();t=time.perf_counter()
source=path("imported_runtime").parent/"models/qwen_ai_detector/inference.py"
spec=importlib.util.spec_from_file_location("imported_qwen",source);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
module.MODEL_ID=str(path("qwen_base"))
saved=json.loads((path("imported_runtime")/"PRAXIS_FINAL_ALL_MODELS_RESULT.json").read_text())
try:
 result=module.analyze_transcript(saved["transcript"]);status=result.get("status","UNKNOWN")
except Exception as exc:result={"error":str(exc),"type":type(exc).__name__};status="ERROR"
report={"started_at":start,"finished_at":datetime.datetime.now(datetime.timezone.utc).isoformat(),"latency_ms":(time.perf_counter()-t)*1000,"status":status,"worker_id":str(os.getpid()),"test_input":"saved transcript, not fresh Whisper output","result":result}
(ROOT/"docs/import-2026-09-29/qwen-smoke.json").write_text(json.dumps(report,indent=2),encoding="utf-8");print(json.dumps(report,indent=2))
