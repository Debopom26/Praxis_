import hashlib
import json
from pathlib import Path

SOURCES = {
    "ecapa": "speechbrain/spkrec-ecapa-voxceleb",
    "minilm": "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
    "qwen_base": "Qwen/Qwen3-0.6B-Base",
    "qwen_performer": "Qwen/Qwen3-0.6B",
    "whisper": "openai/whisper:small",
}


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def verified_model(root: Path, name: str) -> tuple[Path, str]:
    manifest = json.loads((root / "manifest.json").read_text())
    entry = manifest[name]
    directory = (root / name).resolve()
    if entry["source"] != SOURCES[name] or not entry["revision"] or not entry["files"]:
        raise ValueError("Model identity mismatch")
    for relative, expected in entry["files"].items():
        path = (directory / relative).resolve()
        if not path.is_relative_to(directory) or not path.is_file() or digest(path) != expected:
            raise ValueError("Model checksum mismatch")
    return directory, entry["revision"]
