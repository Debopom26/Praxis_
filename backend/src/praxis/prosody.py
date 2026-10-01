import importlib.metadata
from threading import Lock
from time import perf_counter

import numpy as np
import opensmile
import parselmouth
from parselmouth.praat import call

from praxis.contracts import ArtifactState, ModuleStatus
from praxis.evidence import evidence


class Prosody:
    def __init__(self):
        self.lock = Lock()
        self.smile = opensmile.Smile(
            feature_set=opensmile.FeatureSet.eGeMAPSv02,
            feature_level=opensmile.FeatureLevel.Functionals,
        )
        self.version = (
            "opensmile-"
            + importlib.metadata.version("opensmile")
            + "_praat-"
            + parselmouth.__version__
        )

    def analyze(self, window):
        with self.lock:
            return self._analyze(window)

    def _analyze(self, window):
        started = perf_counter()
        wave = window.samples
        rate = window.contract.analysis_sample_rate
        row = self.smile.process_signal(wave, rate).iloc[0]
        features = {
            "egemaps_" + str(k): float(v) if np.isfinite(v) else None for k, v in row.items()
        }
        sound = parselmouth.Sound(wave, sampling_frequency=rate)
        pitch = sound.to_pitch(time_step=0.01, pitch_floor=60, pitch_ceiling=500)
        f0 = pitch.selected_array["frequency"]
        voiced = f0[f0 > 0]
        features.update(
            praat_f0_median=float(np.median(voiced)) if len(voiced) else None,
            praat_f0_range=float(np.ptp(voiced)) if len(voiced) else None,
            praat_f0_variance=float(np.var(voiced)) if len(voiced) else None,
            praat_voiced_ratio=float(np.mean(f0 > 0)),
            praat_energy_rms=float(np.sqrt(np.mean(wave**2))),
            praat_intonation_change=float(np.mean(np.abs(np.diff(voiced))))
            if len(voiced) > 1
            else None,
            praat_voiced_islands_per_second=float(
                np.count_nonzero(np.diff((f0 > 0).astype(int)) == 1) / (len(wave) / rate)
            ),
            source_pause_ratio=1 - 4000 / (window.contract.end_ms - window.contract.start_ms),
        )
        features["praat_jitter_local"] = None
        features["praat_shimmer_local"] = None
        reasons = ["CLASSIFIER_UNVALIDATED", "SPEAKING_RATE_IS_VOICING_PROXY"]
        if len(voiced) >= 20 and not window.contract.quality.reason_codes:
            try:
                pulses = call(sound, "To PointProcess (periodic, cc)", 60, 500)
                jitter = call(pulses, "Get jitter (local)", 0, 0, 0.0001, 0.02, 1.3)
                shimmer = call([sound, pulses], "Get shimmer (local)", 0, 0, 0.0001, 0.02, 1.3, 1.6)
                features["praat_jitter_local"] = float(jitter) if np.isfinite(jitter) else None
                features["praat_shimmer_local"] = float(shimmer) if np.isfinite(shimmer) else None
            except parselmouth.PraatError:
                reasons.append("MICROVARIATION_UNAVAILABLE")
        else:
            reasons.append("MICROVARIATION_UNAVAILABLE")
        return evidence(
            window.contract.call_id,
            window.contract.window_id,
            "prosody",
            self.version,
            ModuleStatus.LOW_QUALITY
            if not len(voiced) or window.contract.quality.reason_codes
            else ModuleStatus.AVAILABLE,
            started,
            features,
            reasons,
            ArtifactState.UNVALIDATED,
        )
