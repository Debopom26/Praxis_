import asyncio
from contextlib import asynccontextmanager
from typing import Protocol

from praxis.contracts import AudioFrame, SessionView, UnavailableEvent
from praxis.contracts.status import ArtifactState, ModuleStatus
from praxis.db.repository import utcnow


class AudioProcessor(Protocol):
    async def process(self, session: SessionView, frame: AudioFrame) -> list: ...
    async def close(self) -> None: ...


class UnavailableProcessor:
    """Explicit absent dependency path, never a simulated analyzer."""

    async def process(self, session: SessionView, frame: AudioFrame) -> list:
        return [
            UnavailableEvent(
                call_id=session.call_id,
                module="audio",
                status=ModuleStatus.UNAVAILABLE,
                artifact_state=ArtifactState.NOT_LOADED,
                reason_codes=["AUDIO_PIPELINE_NOT_CONNECTED"],
                timestamp=utcnow(),
            )
        ]

    async def close(self) -> None:
        return None


class StreamCapacity(Exception):
    pass


class StreamRegistry:
    def __init__(self, limit: int):
        self.limit = limit
        self.active: set[str] = set()
        self.lock = asyncio.Lock()

    async def snapshot(self) -> set[str]:
        async with self.lock:
            return set(self.active)

    @asynccontextmanager
    async def acquire(self, session_id: str):
        async with self.lock:
            if len(self.active) >= self.limit or session_id in self.active:
                raise StreamCapacity()
            self.active.add(session_id)
        try:
            yield
        finally:
            async with self.lock:
                self.active.discard(session_id)
