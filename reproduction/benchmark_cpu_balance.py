import sys,time,json,statistics
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'backend/src'),str(ROOT/'reproduction'),str(ROOT/'reproduction/vendor')]
from local_runtime import decode_baseline_audio
from praxis.supplied.engine import SuppliedEngine
import torch
out=ROOT/'docs/import-2026-09-29/cpu-balance-verified.json'
report={'runs':[]}
def save():out.write_text(json.dumps(report,indent=2))
audio=decode_baseline_audio()[:128000]
e=SuppliedEngine(ROOT/'model_paths.json')
try:
 e.analyze(audio)
 original_whisper=e.whisper
 texts=[]
 def whisper(value):
  r=original_whisper(value);texts.append(r['text']);return r
 e.whisper=whisper
 for threads in (8,6,4,4,6,8):
  e.pool.shutdown(wait=True)
  torch.set_num_threads(threads)
  e.pool=ThreadPoolExecutor(max_workers=5,thread_name_prefix="praxis-tune")
  active=e.pool.submit(torch.get_num_threads).result()
  assert active==threads
  t=time.perf_counter();r=e.analyze(audio);elapsed=time.perf_counter()-t
  row={'threads':threads,'verified_worker_threads':active,'total_s':elapsed,'w2v2_s':r['audit']['w2v2']['latency_ms']/1000,'whisper_s':r['audit']['whisper']['latency_ms']/1000,'same_transcript':texts[-1]==texts[0],'synthetic_score':r['synthetic_voice']['score_0_100'],'experimental_score':r['experimental_score_0_100']}
  report['runs'].append(row);save();print(row,flush=True)
 report['median_s']={str(n):statistics.median(r['total_s'] for r in report['runs'] if r['threads']==n) for n in (4,6,8)}
 report['selected_threads']=int(min(report['median_s'],key=report['median_s'].get));save()
finally:e.close()
