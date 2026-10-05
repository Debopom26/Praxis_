import importlib.metadata as m,json,sys
from pathlib import Path
import torch,torchaudio,fairseq,numpy
root=Path(__file__).resolve().parents[1]
expected={}
for line in (root/"imports/2026-09-29/Praxis_Final_Download/environment/w2v2_python310_pip_freeze.txt").read_text().splitlines():
 if "==" in line:
  name,version=line.split("==",1);expected[name]=version
actual={name:m.version(name) for name in expected}
deltas={name:{"expected":version,"actual":actual[name]} for name,version in expected.items() if actual[name]!=version}
report={"python":sys.version,"executable":sys.executable,"versions":actual,"manifest_differences":deltas,"torch_cpu_operation":torch.ones(2).sum().item(),"cuda_available":torch.cuda.is_available(),"status":"PASS" if not deltas and sys.version_info[:2]==(3,10) else "FAIL"}
(root/"docs/import-2026-09-29/w2v2-environment-verification.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
print(json.dumps({"status":report["status"],"manifest_differences":deltas,"python":sys.version.split()[0],"torch":torch.__version__,"fairseq":fairseq.__version__}))
if report["status"]!="PASS":raise SystemExit(1)
