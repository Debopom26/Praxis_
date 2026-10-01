import sys,time,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'backend/src'),str(ROOT/'reproduction'),str(ROOT/'reproduction/vendor')]
from local_runtime import decode_baseline_audio
from praxis.supplied.engine import SuppliedEngine
from praxis.audio.pipeline import SileroVad
from praxis.supplied.stream import MicrophoneWindows
report={};out=ROOT/'docs/import-2026-09-29/latency-after.json'
def save():out.write_text(json.dumps(report,indent=2))
def measure(fn,*args,**kwargs):
 t=time.perf_counter();r=fn(*args,**kwargs);return round(time.perf_counter()-t,4),r
audio=decode_baseline_audio()[:128000]
e=SuppliedEngine(ROOT/'model_paths.json')
try:
 e.analyze(audio)
 elapsed,result=measure(e.analyze,audio)
 report['after_total_s']=elapsed;report['after_audit']=result['audit'];report['guidance']=result['guidance']['action'];save();print('AFTER',elapsed,flush=True)
 text=json.loads((e.asset('imported_runtime')/'PRAXIS_FINAL_ALL_MODELS_RESULT.json').read_text())['transcript']
 e.qwen.predict(text);elapsed,r=measure(e.qwen.predict,text);report['qwen_long_transcript_s']=elapsed;save()
 stream=MicrophoneWindows(SileroVad());cache={};runs=[]
 for i in range(4):
  t=time.perf_counter();item=stream.push(i,audio[i*32000:(i+1)*32000]);vad_s=time.perf_counter()-t
  if item is not None:
   elapsed,r=measure(e.analyze,item[0],transcript_samples=item[1],text_cache=cache)
   runs.append({'total_s':elapsed,'vad_s':vad_s,'acoustic_samples':len(item[0]),'new_transcript_samples':len(item[1]),'audit':r['audit']})
 report['stream_runs']=runs;report['stream_sustains_two_second_hops']=bool(runs) and all(r['total_s']+r['vad_s']<=2 for r in runs);save()
finally:e.close()
