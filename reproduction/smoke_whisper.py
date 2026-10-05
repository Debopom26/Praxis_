from local_runtime import *
import datetime,time,hashlib
start=datetime.datetime.now(datetime.timezone.utc).isoformat();t=time.perf_counter()
try:
 import torch
 from transformers import WhisperProcessor,WhisperForConditionalGeneration
 processor=WhisperProcessor.from_pretrained(str(path("whisper")),local_files_only=True)
 model=WhisperForConditionalGeneration.from_pretrained(str(path("whisper")),local_files_only=True).eval()
 audio=decode_audio()[:480000]
 inputs=processor(audio,sampling_rate=16000,return_tensors="pt",return_attention_mask=True)
 with torch.inference_mode(): ids=model.generate(**inputs,max_new_tokens=128)
 text=processor.batch_decode(ids,skip_special_tokens=True)[0]
 result={"status":"AVAILABLE","generated_tokens":int(ids.shape[-1]),"transcript_sha256":hashlib.sha256(text.encode()).hexdigest(),"input_duration_s":len(audio)/16000,"test_kind":"first_30s_independent_smoke_not_baseline_transcript"}
except Exception as exc:result={"status":"ERROR","error":str(exc),"type":type(exc).__name__}
report={"started_at":start,"finished_at":datetime.datetime.now(datetime.timezone.utc).isoformat(),"latency_ms":(time.perf_counter()-t)*1000,"worker_id":str(os.getpid()),**result}
(ROOT/"docs/import-2026-09-29/whisper-smoke.json").write_text(json.dumps(report,indent=2),encoding="utf-8");print(json.dumps(report,indent=2))
