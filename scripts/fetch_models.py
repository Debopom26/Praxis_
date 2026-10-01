"""Fetch only the five permitted pretrained models using the committed revision/hash inventory."""
import hashlib
import json
from pathlib import Path
import urllib.request

root = Path(__file__).resolve().parents[1]
inventory = json.loads((root / "docs/model-assets.json").read_text(encoding="utf-8"))
allowed = {"whisper", "ecapa", "minilm", "qwen_base", "qwen_performer"}
if set(inventory) != allowed:
    raise ValueError("Unexpected model scope")
artifacts = root / "artifacts"

def checksum(path):
    value = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024*1024), b""):
            value.update(chunk)
    return value.hexdigest()

for name, info in inventory.items():
    directory = artifacts / name
    for relative, expected in info["files"].items():
        path = (directory / relative).resolve()
        if not path.is_relative_to(directory.resolve()):
            raise ValueError("Invalid inventory path")
        if path.exists():
            if checksum(path) != expected:
                raise ValueError("Existing asset checksum mismatch: " + name + "/" + relative)
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        url = ("https://openaipublic.azureedge.net/main/whisper/models/" + expected + "/small.pt") if name == "whisper" else ("https://huggingface.co/" + info["source"] + "/resolve/" + info["revision"] + "/" + relative)
        temporary = path.with_suffix(path.suffix + ".part")
        print("Downloading", name, relative, flush=True)
        urllib.request.urlretrieve(url, temporary)
        if checksum(temporary) != expected:
            raise ValueError("Downloaded checksum mismatch")
        temporary.replace(path)
(artifacts / "manifest.json").write_text(json.dumps(inventory, indent=2), encoding="utf-8")
print("Verified all permitted model assets. No datasets or deferred models downloaded.")
