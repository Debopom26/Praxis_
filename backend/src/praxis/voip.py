"""Tenant-scoped, memory-only two-party voice relay for Praxis-owned calls.

The relay carries 20 ms, 16 kHz, mono PCM16 frames. It never persists audio.
Run with one backend worker; this is deliberately a single-process call registry.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from uuid import uuid4

from fastapi import WebSocket

from praxis.security import Principal

FRAME_BYTES = 640
logger = logging.getLogger("praxis.voip")


@dataclass(eq=False)
class Peer:
    principal: Principal
    socket: WebSocket
    send_lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    call_id: str | None = None
    send_timeouts: int = 0
    frames_in: int = 0
    frames_out: int = 0

    async def send(self, value: dict | bytes) -> None:
        async with self.send_lock:
            if isinstance(value, bytes):
                await self.socket.send_bytes(value)
            else:
                await self.socket.send_json(value)


@dataclass
class Call:
    id: str
    caller: Peer
    callee: Peer
    active: bool = False
    expiry: asyncio.Task | None = None


class VoipHub:
    def __init__(self) -> None:
        self.lock = asyncio.Lock()
        self.peers: dict[tuple[str, str], Peer] = {}
        self.calls: dict[str, Call] = {}

    async def active_refs(self) -> set[tuple[str, str, str]]:
        """Tenant, owner and call IDs whose two-party audio relay is active."""
        async with self.lock:
            return {
                (peer.principal.tenant_id, peer.principal.user_id, call.id)
                for call in self.calls.values() if call.active
                for peer in (call.caller, call.callee)
            }

    async def register(self, peer: Peer) -> bool:
        key = (peer.principal.tenant_id, peer.principal.user_id)
        async with self.lock:
            if key in self.peers:
                return False
            self.peers[key] = peer
            return True

    async def unregister(self, peer: Peer) -> None:
        async with self.lock:
            key = (peer.principal.tenant_id, peer.principal.user_id)
            if self.peers.get(key) is peer:
                del self.peers[key]
        await self.hangup(peer)

    async def invite(self, caller: Peer, callee_id: str, caller_name: str) -> None:
        async with self.lock:
            callee = self.peers.get((caller.principal.tenant_id, callee_id))
            if caller.call_id or not callee or callee is caller or callee.call_id:
                callee = None
            else:
                call = Call(str(uuid4()), caller, callee)
                caller.call_id = call.id
                callee.call_id = call.id
                self.calls[call.id] = call
                call.expiry = asyncio.create_task(self._expire(call))
        if callee is None:
            await caller.send({"type": "unavailable"})
            return
        try:
            await callee.send({"type": "ring", "call_id": call.id, "from": caller_name})
            await caller.send({"type": "dialing", "call_id": call.id})
        except Exception:
            await self.hangup(caller)

    async def _expire(self, call: Call) -> None:
        try:
            await asyncio.sleep(30)
            await self.hangup(call.caller, "timeout")
        except asyncio.CancelledError:
            pass

    async def accept(self, peer: Peer, call_id: str) -> None:
        async with self.lock:
            call = self.calls.get(call_id)
            if not call or call.callee is not peer or call.active:
                return
            call.active = True
            if call.expiry and call.expiry is not asyncio.current_task():
                call.expiry.cancel()
            caller, callee = call.caller, call.callee
        try:
            await asyncio.gather(
                caller.send({"type": "active", "call_id": call_id}),
                callee.send({"type": "active", "call_id": call_id}),
            )
        except Exception:
            await self.hangup(peer)

    async def hangup(self, peer: Peer, reason: str = "ended") -> None:
        async with self.lock:
            call = self.calls.get(peer.call_id or "")
            if not call or peer not in (call.caller, call.callee):
                return
            del self.calls[call.id]
            call.caller.call_id = None
            call.callee.call_id = None
            if call.expiry and call.expiry is not asyncio.current_task():
                call.expiry.cancel()
            other = call.callee if peer is call.caller else call.caller
            logger.info(
                "voip_call_ended reason=%s caller_in=%s caller_out=%s callee_in=%s callee_out=%s",
                reason, call.caller.frames_in, call.caller.frames_out,
                call.callee.frames_in, call.callee.frames_out,
            )
        for recipient in (peer, other):
            try:
                await recipient.send({"type": "ended", "call_id": call.id, "reason": reason})
            except Exception:
                logger.debug("call_end_notification_unavailable")

    async def relay(self, peer: Peer, frame: bytes) -> bool:
        if len(frame) != FRAME_BYTES:
            return False
        async with self.lock:
            call = self.calls.get(peer.call_id or "")
            if not call or not call.active or peer not in (call.caller, call.callee):
                return False
            other = call.callee if peer is call.caller else call.caller
            peer.frames_in += 1
        try:
            await asyncio.wait_for(other.send(frame), timeout=1.0)
            other.send_timeouts = 0
            other.frames_out += 1
            if peer.frames_in % 250 == 0:
                logger.info("voip_media_progress sender_in=%s receiver_out=%s",
                            peer.frames_in, other.frames_out)
            return True
        except asyncio.TimeoutError:
            other.send_timeouts += 1
            logger.warning("voip_peer_send_timeout count=%s", other.send_timeouts)
            if other.send_timeouts < 3:
                return True  # Drop a late frame instead of ending both sides immediately.
            await self.hangup(peer, "peer_unresponsive")
            return False
        except Exception as exc:
            logger.warning("voip_peer_send_failed type=%s", type(exc).__name__)
            await self.hangup(peer)
            return False
