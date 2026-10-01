from local_runtime import *
import numpy as np
from fusion_features_v2 import PraxisFusionFeaturesV2
from risk_engine_v2 import PraxisRiskEngineV2
saved=json.loads((path("imported_runtime")/"PRAXIS_FINAL_ALL_MODELS_RESULT.json").read_text())
audio=decode_baseline_audio(); windows=baseline_windows(audio)
e=saved["evidence"]
q=dict(e["qwen"],probability=e["qwen"]["ai_script_probability"],available=True,status="AVAILABLE")
c=dict(e["context"].get("features",{}),available=True,status="AVAILABLE")
f=PraxisFusionFeaturesV2().build(w2v2=e["w2v2"],minilm=e["minilm"],rules=e["rules"],qwen=q,context=c,ecapa=e["ecapa"])
r=PraxisRiskEngineV2().score(f)
report={"test_kind":"runner_contract_and_saved_evidence_replay_NOT_FRESH_E2E","audio_samples":len(audio),"window_count":len(windows),"last_window_tile_padded":True,"risk_score":r["risk_score"],"regressor_status":r["regressor_status"],"policy":r["policy_action"],"context_forced_available_by_original_runner":True,"exact_saved_risk_match":r["risk_score"]==saved["risk"]["risk_score"]}
assert len(windows)==54,report
assert report["exact_saved_risk_match"],report
(ROOT/"docs/import-2026-09-29/baseline-contract-replay.json").write_text(json.dumps(report,indent=2),encoding="utf-8");print(json.dumps(report,indent=2))
