import json
from math import gcd
from pathlib import Path
from threading import Lock
from time import perf_counter
from uuid import uuid4

import numpy as np
from scipy.signal import resample_poly

from praxis.artifacts import verified_model
from praxis.audio.pipeline import SileroVad, quality
from praxis.contracts import ArtifactState, ModuleStatus, Provenance, SpeakerEvidence, SpeakerState
from praxis.db.models import SpeakerProfile
from praxis.db.repository import utcnow
from praxis.security import Encryption, require_role


def cosine(left: np.ndarray, right: np.ndarray) -> float:
    a = np.asarray(left, dtype=float).reshape(-1)
    b = np.asarray(right, dtype=float).reshape(-1)
    if (
        a.shape != b.shape
        or not len(a)
        or not np.isfinite(a).all()
        or not np.isfinite(b).all()
        or np.linalg.norm(a) == 0
        or np.linalg.norm(b) == 0
    ):
        raise ValueError("Invalid compatible embeddings required")
    return float(np.clip(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)), -1, 1))


class ECAPA:
    def __init__(self, artifacts: Path):
        import torch
        from speechbrain.inference.speaker import EncoderClassifier
        from speechbrain.utils.fetching import LocalStrategy

        directory, self.version = verified_model(artifacts, "ecapa")
        self.torch = torch
        self.lock = Lock()
        self.model = EncoderClassifier.from_hparams(
            source=str(directory),
            savedir=str(artifacts.parent / ".cache" / "ecapa-runtime"),
            overrides={"pretrained_path": str(directory).replace("\\", "/")},
            run_opts={"device": "cpu"},
            local_strategy=LocalStrategy.COPY,
        )

    def embed(self, samples: np.ndarray, rate: int) -> np.ndarray:
        factor = gcd(rate, 16000)
        wave = resample_poly(samples, 16000 // factor, rate // factor).astype(np.float32)
        if not 1 <= len(wave) / 16000 <= 60:
            raise ValueError("Speaker speech duration invalid")
        with self.lock, self.torch.inference_mode():
            result = (
                self.model.encode_batch(self.torch.from_numpy(wave).unsqueeze(0))
                .detach()
                .cpu()
                .numpy()
                .reshape(-1)
            )
        if result.size != 192 or not np.isfinite(result).all() or np.linalg.norm(result) == 0:
            raise ValueError("Invalid ECAPA embedding")
        return result


def voiced_clip(samples, rate):
    vad = SileroVad()
    factor = gcd(rate, 16000)
    wave = resample_poly(samples, 16000 // factor, rate // factor).astype(np.float32)
    parts = [
        wave[start : start + 512]
        for start in range(0, len(wave) - 511, 512)
        if vad.speech(wave[start : start + 512])
    ]
    return np.concatenate(parts) if parts else np.empty(0, np.float32)


class SpeakerService:
    def __init__(self, repo, embedder: ECAPA, encryption: Encryption):
        self.repo = repo
        self.embedder = embedder
        self.encryption = encryption

    def enroll(
        self,
        principal,
        session_id: str,
        identity: str,
        clips: list[tuple[np.ndarray, int]],
        approved: bool,
        originals: list[str] | None = None,
    ):
        require_role(principal, "admin")
        self.repo.get(principal, session_id)
        if not approved or not 3 <= len(clips) <= 10:
            raise ValueError("Three to ten approved clean clips required")
        accepted = []
        for samples, rate in clips:
            if quality(samples, rate).reason_codes:
                raise ValueError("Enrollment clip fails quality gate")
            voiced = voiced_clip(samples, rate)
            if len(voiced) < 16000:
                raise ValueError("Each enrollment clip needs voiced speech")
            accepted.append(voiced)
        if sum(map(len, accepted)) < 15 * 16000:
            raise ValueError("At least fifteen voiced seconds required")
        centroid = np.mean([self.embedder.embed(s, 16000) for s in accepted], axis=0)
        cosine(centroid, centroid)  # Reject nonfinite/zero centroids before storing them.
        version = str(uuid4())
        encrypted = self.encryption.encrypt(
            json.dumps(centroid.tolist()).encode(), principal.tenant_id, identity, version
        )
        with self.repo.sessions.begin() as db:
            row = db.get(SpeakerProfile, (principal.tenant_id, identity))
            if row is None:
                row = SpeakerProfile(tenant_id=principal.tenant_id, identity=identity)
                db.add(row)
            row.version = version
            row.model_version = self.embedder.version
            row.encrypted_centroid = encrypted
            row.approved_by = principal.user_id
            row.created_at = utcnow()
            if self.repo.privacy is not None and originals:
                self.repo.privacy.retain(
                    db,
                    principal,
                    session_id,
                    "enrollment",
                    json.dumps({"clips_base64": originals}).encode(),
                    identity,
                )
            self.repo._audit(
                db,
                principal,
                session_id,
                "speaker_enrollment_updated",
                ["CONTROLLED_ENROLLMENT"],
                profile_version=version,
                model_versions={"speaker": self.embedder.version},
            )
        return {
            "profile_version": version,
            "model_version": self.embedder.version,
            "threshold_state": "UNVALIDATED",
        }

    def verify(self, principal, session, window):
        started = perf_counter()
        similarity = None
        profile_version = None
        status = ModuleStatus.UNAVAILABLE
        reasons = ["NOT_ENROLLED"]
        if session.claimed_identity:
            with self.repo.sessions() as db:
                row = db.get(SpeakerProfile, (principal.tenant_id, session.claimed_identity))
                if row:
                    if row.model_version != self.embedder.version:
                        reasons = ["MODEL_VERSION_MISMATCH"]
                    else:
                        stored = np.array(
                            json.loads(
                                self.encryption.decrypt(
                                    row.encrypted_centroid,
                                    principal.tenant_id,
                                    row.identity,
                                    row.version,
                                )
                            )
                        )
                        profile_version = row.version
            if profile_version is not None:
                # Release the database connection before model inference.
                similarity = cosine(
                    self.embedder.embed(window.samples, window.contract.analysis_sample_rate),
                    stored,
                )
                status = (
                    ModuleStatus.LOW_QUALITY
                    if window.contract.quality.reason_codes
                    else ModuleStatus.AVAILABLE
                )
                reasons = ["THRESHOLDS_UNVALIDATED", *window.contract.quality.reason_codes]
        return SpeakerEvidence(
            call_id=session.call_id,
            window_id=window.contract.window_id,
            module="speaker",
            model_version=self.embedder.version,
            status=status,
            latency_ms=(perf_counter() - started) * 1000,
            reason_codes=reasons,
            provenance=Provenance(model_version=self.embedder.version),
            timestamp=utcnow(),
            speaker_state=SpeakerState.UNAVAILABLE,
            cosine_similarity=similarity,
            profile_version=profile_version,
            threshold_state=ArtifactState.UNVALIDATED,
        )
