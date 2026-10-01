from local_runtime import *
import datetime,time,hashlib
start=datetime.datetime.now(datetime.timezone.utc).isoformat();t=time.perf_counter()
try:
 from transformers import pipeline
 audio=decode_baseline_audio()
 model=pipeline(task="automatic-speech-recognition",model=str(path("whisper")),device=-1,chunk_length_s=30)
 output=model({"array":audio,"sampling_rate":16000})
 transcript=str(output.get("text","")).strip()
 saved=json.loads((path("imported_runtime")/"PRAXIS_FINAL_ALL_MODELS_RESULT.json").read_text())
 result={"status":"AVAILABLE" if transcript else "ERROR","word_count":len(transcript.split()),"saved_word_count":saved["word_count"],"exact_transcript_match":transcript==saved["transcript"],"transcript_sha256":hashlib.sha256(transcript.encode()).hexdigest(),"audio_samples":len(audio),"windows":len(baseline_windows(audio)),"decoder":"librosa.load(sr=16000,mono=True) via FFmpeg"}
except Exception as exc:result={"status":"ERROR","error":str(exc),"type":type(exc).__name__}
report={"started_at":start,"finished_at":datetime.datetime.now(datetime.timezone.utc).isoformat(),"latency_ms":(time.perf_counter()-t)*1000,"worker_id":str(os.getpid()),**result}
(ROOT/"docs/import-2026-09-29/whisper-full-reproduction.json").write_text(json.dumps(report,indent=2),encoding="utf-8");print(json.dumps(report,indent=2))
