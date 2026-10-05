import sys,time,json,os
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'backend/src'),str(ROOT/'reproduction'),str(ROOT/'reproduction/vendor')]
from local_runtime import decode_baseline_audio
from praxis.supplied.engine import SuppliedEngine
import torch,numpy as np
out=ROOT/'docs/import-2026-09-29/latency-before.json'
report={'logical_cpus':os.cpu_count(),'cuda':torch.cuda.is_available(),'audio_seconds':8,'runs':{}}
def save():out.write_text(json.dumps(report,indent=2))
def measure(fn,*args):
 t=time.perf_counter();r=fn(*args);return round(time.perf_counter()-t,4),r
audio=decode_baseline_audio()[:128000]
e=SuppliedEngine(ROOT/'model_paths.json')
try:
 e.analyze(audio)
 elapsed,result=measure(e.analyze,audio)
 report['before_total_s']=elapsed;report['before_audit']=result['audit'];save();print('BEFORE',elapsed,flush=True)
 text=json.loads((e.asset('imported_runtime')/'PRAXIS_FINAL_ALL_MODELS_RESULT.json').read_text())['transcript']
 for name,fn,args in [('qwen',e.qwen.predict,(text,)),('minilm',e.minilm.analyze,(text,)),('prosody',e.prosody.analyze,(audio,)),('rules',e.rules.analyze,(text,)),('context',e.context.analyze,())]:
  fn(*args);elapsed,r=measure(fn,*args);report['runs'][name]={'seconds':elapsed,'status':r.get('status')};save()
 # Synthetic reference is only for embedding timing, never enrolled or treated as identity evidence.
 ref=np.ones(192,dtype=np.float32)
 e.speaker(audio,ref);elapsed,r=measure(e.speaker,audio,ref);report['runs']['ecapa']={'seconds':elapsed,'status':r['status'],'identity_test':False};save()
 reference=None
 for threads in (2,4,8):
  torch.set_num_threads(threads)
  with torch.inference_mode():
   elapsed,r=measure(e.whisper,{'array':audio,'sampling_rate':16000})
  if reference is None:reference=r['text']
  report['runs']['whisper_threads_'+str(threads)]={'seconds':elapsed,'same_transcript':r['text']==reference}
  save();print('WHISPER',threads,elapsed,flush=True)
finally:e.close()
