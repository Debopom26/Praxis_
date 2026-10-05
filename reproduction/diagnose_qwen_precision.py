from local_runtime import *
import importlib.util,time,torch
source=path("imported_runtime").parent/"models/qwen_ai_detector/inference.py"
spec=importlib.util.spec_from_file_location("qwen_precision",source);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);module.MODEL_ID=str(path("qwen_base"))
saved=json.loads((path("imported_runtime")/"PRAXIS_FINAL_ALL_MODELS_RESULT.json").read_text())
detector=module.QwenAIScriptDetector(device="cpu")
rows=[]
for dtype in [torch.float32,torch.float16]:
 detector.model.to(dtype=dtype)
 try:
  result=detector.predict(saved["transcript"])
  rows.append({"dtype":str(dtype),"result":result})
 except Exception as exc: rows.append({"dtype":str(dtype),"error":str(exc)})
report={"test_kind":"precision_diagnostic_CPU_not_baseline_substitution","saved_probability":saved["evidence"]["qwen"]["ai_script_probability"],"variants":rows}
(ROOT/"docs/import-2026-09-29/qwen-precision-diagnostic.json").write_text(json.dumps(report,indent=2),encoding="utf-8");print(json.dumps(report,indent=2))
