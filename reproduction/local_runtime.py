"""Offline reproduction helpers. Imported artifacts and backend remain unchanged."""
import json, os, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
CONFIG = json.loads((ROOT / "model_paths.json").read_text(encoding="utf-8"))
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / "reproduction/vendor"))
def path(name):
    value = (ROOT / CONFIG["models"][name]["path"]).resolve()
    if not value.exists(): raise FileNotFoundError(value)
    return value
sys.path.insert(0, str(path("imported_runtime")))
def decode_audio():
    import av, numpy as np
    source = CONFIG["baseline_audio"]["path"]
    if os.name != "nt" and source.startswith("C:/"):
        source = "/mnt/c/" + source[3:]
    chunks = []
    with av.open(source) as container:
        resampler = av.AudioResampler(format="fltp", layout="mono", rate=16000)
        for frame in container.decode(audio=0):
            chunks.extend(f.to_ndarray().reshape(-1) for f in resampler.resample(frame))
        chunks.extend(f.to_ndarray().reshape(-1) for f in resampler.resample(None))
    return np.concatenate(chunks).astype(np.float32)

def decode_baseline_audio():
    import imageio_ffmpeg, librosa, audioread.ffdec
    source = CONFIG["baseline_audio"]["path"]
    # Librosa's M4A fallback uses FFmpeg -> signed 16-bit PCM, then its default resampler.
    # Keep decoder substitution scoped to this isolated reproduction process.
    audioread.ffdec.COMMANDS = (imageio_ffmpeg.get_ffmpeg_exe(),)
    audio, sr = librosa.load(source, sr=16000, mono=True)
    return audio

def baseline_windows(audio):
    import numpy as np, math
    window, hop = 64000, 32000
    if len(audio) == 0: raise ValueError("Empty audio")
    result=[]; start=0
    while start < len(audio):
        chunk=audio[start:start+window]
        if len(chunk)<window: chunk=np.tile(chunk,math.ceil(window/len(chunk)))[:window]
        result.append(chunk.astype(np.float32))
        if start+window>=len(audio): break
        start+=hop
    return result
