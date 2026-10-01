from io import BytesIO

import numpy as np
import soundfile as sf


def decode_clip(payload: bytes, max_seconds: float = 60) -> tuple[np.ndarray, int]:
    """Bounded WAV/FLAC decode; compressed external formats are deliberately rejected."""
    if not payload or len(payload) > 20 * 1024 * 1024:
        raise ValueError("Empty or oversized audio")
    try:
        with sf.SoundFile(BytesIO(payload)) as audio:
            if (
                audio.format not in {"WAV", "FLAC"}
                or audio.channels not in (1, 2)
                or not 8000 <= audio.samplerate <= 48000
                or not 0 < audio.frames <= max_seconds * audio.samplerate
            ):
                raise ValueError("Unsupported audio format or duration")
            samples = audio.read(dtype="float32", always_2d=True).mean(axis=1)
            rate = audio.samplerate
    except (sf.LibsndfileError, RuntimeError) as exc:
        raise ValueError("Malformed audio") from exc
    if not np.isfinite(samples).all() or np.max(np.abs(samples)) > 1:
        raise ValueError("Audio samples outside valid amplitude range")
    return samples, rate
