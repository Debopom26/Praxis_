import sys,time,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'backend/src'),str(ROOT/'reproduction'),str(ROOT/'reproduction/vendor')]
from local_runtime import decode_baseline_audio
from praxis.supplied.engine import SuppliedEngine
from praxis.supplied.whisper_execution import reuse_encoder
import torch
report={};out=ROOT/'docs/import-2026-09-29/encoder-reuse-benchmark.json'
def save():out.write_text(json.dumps(report,indent=2))
def measure(fn,*args,**kwargs):
 t=time.perf_counter();r=fn(*args,**kwargs);return round(time.perf_counter()-t,4),r
audio=decode_baseline_audio()[:128000]
e=SuppliedEngine(ROOT/'model_paths.json')
# Explicit original-library baseline after optimization becomes the runtime default.
e.whisper.model.generate = getattr(e.whisper.model.generate, '__wrapped__', e.whisper.model.generate)
try:
 e.analyze(audio)
 elapsed,r=measure(e.analyze,audio);report['before_total_s']=elapsed;report['before_audit']=r['audit'];save();print('BEFORE',elapsed,flush=True)
 cases=[audio,audio[:64000],audio[64000:96000],audio[96000:128000]]
 originals=[];counts=[];counter=[0]
 hook=e.whisper.model.get_encoder().register_forward_hook(lambda *args:counter.__setitem__(0,counter[0]+1))
 for clip in cases:
  counter[0]=0
  with torch.inference_mode():elapsed,r=measure(e.whisper,{'array':clip,'sampling_rate':16000})
  originals.append(r['text']);counts.append({'before_s':elapsed,'before_encoder_calls':counter[0]})
 report['cases']=counts;save()
 original_generate=reuse_encoder(e.whisper)
 for i,clip in enumerate(cases):
  counter[0]=0
  with torch.inference_mode():elapsed,r=measure(e.whisper,{'array':clip,'sampling_rate':16000})
  counts[i].update(after_s=elapsed,after_encoder_calls=counter[0],identical_transcript=r['text']==originals[i])
  save();print('CASE',i,counts[i],flush=True)
 assert all(v['identical_transcript'] for v in counts)
 elapsed,r=measure(e.analyze,audio);report['after_total_s']=elapsed;report['after_audit']=r['audit'];save();print('AFTER',elapsed,flush=True)
 hook.remove()
finally:e.close()
