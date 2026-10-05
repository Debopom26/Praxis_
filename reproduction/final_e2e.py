"""Fresh local E2E reproduction, preserving imported model/artifact implementations."""
from local_runtime import *
import datetime,hashlib,importlib.util,io,numpy as np,subprocess,time
from minilm_local import PraxisMiniLMInference
from context_engine import PraxisContextEngine
from rules_engine import PraxisRulesEngine
from adapters.prosody_feature_adapter import PraxisProsodyFeatureAdapter
from fusion_features_v2 import PraxisFusionFeaturesV2
from risk_engine_v2 import PraxisRiskEngineV2
OUTPUT=ROOT/"docs/import-2026-09-29/final-e2e-local.json"
report={"kind":"FRESH_LOCAL_E2E","status":"RUNNING","execution_order":"original sequential baseline; backend parallel integration remains separate","modules":{}}
def save():OUTPUT.write_text(json.dumps(report,indent=2),encoding="utf-8")
def call(name,fn):
 start=datetime.datetime.now(datetime.timezone.utc).isoformat();t=time.perf_counter()
 try:
  value=fn();status="SUCCESS"
 except Exception as exc:
  report["modules"][name]={"status":"ERROR","error":str(exc),"started_at":start,"finished_at":datetime.datetime.now(datetime.timezone.utc).isoformat(),"latency_ms":(time.perf_counter()-t)*1000,"worker_id":str(os.getpid())};report["status"]="FAILED";save();raise
 report["modules"][name]={"status":status,"started_at":start,"finished_at":datetime.datetime.now(datetime.timezone.utc).isoformat(),"latency_ms":(time.perf_counter()-t)*1000,"worker_id":str(os.getpid())};save();print(name,status,flush=True);return value
source=Path(CONFIG["baseline_audio"]["path"])
assert hashlib.sha256(source.read_bytes()).hexdigest()==CONFIG["baseline_audio"]["sha256"]
audio=call("decode",decode_baseline_audio)
windows=np.stack(baseline_windows(audio));assert windows.shape==(54,64000)
def w2v2():
 payload=io.BytesIO();np.save(payload,windows,allow_pickle=False)
 interpreter=CONFIG["w2v2_environment"]["python"]
 command=["wsl","-d",CONFIG["w2v2_environment"]["distribution"],"--","sh","-lc",f"cd /mnt/c/Users/KIIT/Downloads/Praxis_ && {interpreter} -u -B reproduction/w2v2_worker_local.py"]
 with (ROOT/"docs/import-2026-09-29/w2v2-inference.log").open("w",encoding="utf-8") as log:
  process=subprocess.Popen(command,stdin=subprocess.PIPE,stdout=log,stderr=subprocess.STDOUT);process.communicate(payload.getvalue())
 if process.returncode:raise RuntimeError("W2V2 worker failed; inspect w2v2-inference.log")
 results=json.loads((ROOT/"docs/import-2026-09-29/w2v2-local-results.json").read_text())["results"]
 if len(results)!=54 or not all(r.get("available") for r in results):raise RuntimeError("W2V2 did not pass all 54 windows")
 return dict(max(results,key=lambda r:r["spoof_softmax"]),available=True,status="AVAILABLE",window_count=len(results))
w=call("w2v2",w2v2);del windows
def whisper():
 from transformers import pipeline
 model=pipeline(task="automatic-speech-recognition",model=str(path("whisper")),device=-1,chunk_length_s=30)
 text=str(model({"array":audio,"sampling_rate":16000}).get("text","")).strip()
 if not text:raise RuntimeError("Empty Whisper transcript")
 return text
transcript=call("whisper",whisper)
mini=call("minilm",lambda:PraxisMiniLMInference(path("minilm_trained"),device="cpu",local_model_path=path("minilm_base")).analyze(transcript))
assert list(mini["probabilities"])==CONFIG["locked_labels"]
rules=call("rules",lambda:PraxisRulesEngine().analyze(transcript))
def qwen():
 src=path("imported_runtime").parent/"models/qwen_ai_detector/inference.py"
 spec=importlib.util.spec_from_file_location("e2e_qwen",src);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);m.MODEL_ID=str(path("qwen_base"))
 return m.QwenAIScriptDetector(device="cpu").predict(transcript)
q=call("qwen",qwen)
context=call("context",lambda:PraxisContextEngine().analyze())
prosody=call("prosody",lambda:PraxisProsodyFeatureAdapter(path("prosody")).analyze(audio))
assert prosody["finite_feature_count"]==98 and prosody["available"]
assert mini["available"] and q["status"]=="OK" and rules["status"]=="AVAILABLE"
ecapa={"available":False,"status":"UNAVAILABLE","reason":"NO_ENROLLED_TRUSTED_SPEAKER"}
q_fusion=dict(q,available=True,status="AVAILABLE",probability=q["ai_script_probability"])
# Preserve unknown host metadata; do not repeat historical forced AVAILABLE behavior.
context_fusion=dict(context.get("features",{}),available=context["available_features"]>0,status=context["status"])
fusion=call("fusion",lambda:PraxisFusionFeaturesV2().build(w2v2=w,minilm=mini,rules=rules,qwen=q_fusion,context=context_fusion,ecapa=ecapa,prosody=prosody))
risk=call("risk_policy",lambda:PraxisRiskEngineV2().score(fusion))
saved=json.loads((path("imported_runtime")/"PRAXIS_FINAL_ALL_MODELS_RESULT.json").read_text())
report.update(status="COMPLETE",audio_sha256=CONFIG["baseline_audio"]["sha256"],transcript_sha256=hashlib.sha256(transcript.encode()).hexdigest(),word_count=len(transcript.split()),exact_saved_transcript_match=transcript==saved["transcript"],w2v2=w,minilm=mini,qwen=q,rules=rules,context=context,prosody={k:v for k,v in prosody.items() if k!="features"},ecapa=ecapa,fusion=fusion,risk=risk,policy=risk["policy_action"],historical_context_status_difference="Original runner forced AVAILABLE for unknown metadata; local run preserves truthful evidence availability",qwen_variation_accepted_by_user=True)
report["baseline_comparison"]={"w2v2_54_windows":w["window_count"]==54,"w2v2_peak_float32_atol_1e_6":abs(w["spoof_softmax"]-0.9998408555984497)<=1e-6,"whisper_exact_transcript":report["exact_saved_transcript_match"],"minilm_locked_8_outputs":len(mini["probabilities"])==8,"prosody_98_finite":prosody["finite_feature_count"]==98,"risk_rounded_97_46":round(risk["risk_score"],2)==97.46,"policy_hold":risk["policy_action"]=="HOLD","bootstrap_status_preserved":risk["regressor_status"]=="BOOTSTRAP_UNTRAINED"}
report["baseline_pass"]=all(report["baseline_comparison"].values())
report["status"]="PASS_WITH_DOCUMENTED_DIFFERENCES" if report["baseline_pass"] else "BASELINE_MISMATCH"
save();print(json.dumps({"status":report["status"],"w2v2":w["spoof_softmax"],"risk":risk["risk_score"],"policy":risk["policy_action"],"regressor_status":risk["regressor_status"]}),flush=True)
