from local_runtime import *
import datetime,time
start=datetime.datetime.now(datetime.timezone.utc).isoformat();t=time.perf_counter()
try:
 import torch,soundfile as sf
 from speechbrain.inference.speaker import SpeakerRecognition
 from speechbrain.utils.fetching import LocalStrategy
 source=path("ecapa")
 model=SpeakerRecognition.from_hparams(source=str(source),savedir=str(ROOT/"reproduction/ecapa-local"),overrides={"pretrained_path":str(source)},local_strategy=LocalStrategy.COPY,run_opts={"device":"cpu"})
 audio,sr=sf.read(source/"example1.wav",dtype="float32")
 assert sr==16000
 with torch.inference_mode(): emb=model.encode_batch(torch.from_numpy(audio).unsqueeze(0))
 assert torch.isfinite(emb).all()
 result={"status":"AVAILABLE","embedding_shape":list(emb.shape),"finite":True,"test_input":"bundled public example1.wav","identity_verification":"NOT_RUN_NO_TRUSTED_ENROLLMENT"}
except Exception as exc:result={"status":"ERROR","error":str(exc),"type":type(exc).__name__}
report={"started_at":start,"finished_at":datetime.datetime.now(datetime.timezone.utc).isoformat(),"latency_ms":(time.perf_counter()-t)*1000,"worker_id":str(os.getpid()),**result}
(ROOT/"docs/import-2026-09-29/ecapa-smoke.json").write_text(json.dumps(report,indent=2),encoding="utf-8");print(json.dumps(report,indent=2))
