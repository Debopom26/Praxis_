import base64
import json
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from threading import Lock
from time import monotonic

import jwt
from argon2 import PasswordHasher, Type
from argon2.exceptions import InvalidHashError, VerificationError
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from praxis.config import Settings

PASSWORD_HASHER = PasswordHasher(type=Type.ID)


def hash_password(password: str) -> str:
    if not 12 <= len(password) <= 1024:
        raise ValueError("Password must contain 12 to 1024 characters")
    return PASSWORD_HASHER.hash(password)


def verify_password(encoded: str, password: str) -> bool:
    try:
        return PASSWORD_HASHER.verify(encoded, password)
    except (VerificationError, InvalidHashError):
        return False


@dataclass(frozen=True)
class Principal:
    user_id: str
    tenant_id: str
    role: str


class AccessDenied(Exception):
    pass


class Tokens:
    def __init__(self, settings: Settings):
        self.settings = settings

    def issue(self, user_id: str, tenant_id: str) -> str:
        now = datetime.now(timezone.utc)
        return jwt.encode(
            dict(
                sub=user_id,
                tenant_id=tenant_id,
                jti=secrets.token_urlsafe(24),
                iat=now,
                nbf=now,
                exp=now + timedelta(minutes=self.settings.token_ttl_minutes),
                iss=self.settings.jwt_issuer,
                aud=self.settings.jwt_audience,
            ),
            self.settings.jwt_secret.get_secret_value(),
            algorithm="HS256",
        )

    def decode(self, token: str) -> tuple[str, str]:
        try:
            p = jwt.decode(
                token,
                self.settings.jwt_secret.get_secret_value(),
                algorithms=["HS256"],
                issuer=self.settings.jwt_issuer,
                audience=self.settings.jwt_audience,
                options={"require": ["sub", "tenant_id", "jti", "iat", "nbf", "exp", "iss", "aud"]},
            )
            if not isinstance(p["sub"], str) or not isinstance(p["tenant_id"], str):
                raise AccessDenied()
            return p["sub"], p["tenant_id"]
        except jwt.PyJWTError as exc:
            raise AccessDenied() from exc


class Encryption:
    def __init__(self, key_base64: str):
        key = base64.b64decode(key_base64, validate=True)
        if len(key) != 32:
            raise ValueError("AES-256 key required")
        self.aes = AESGCM(key)

    @staticmethod
    def associated_data(tenant: str, identity: str, version: str) -> bytes:
        return json.dumps([tenant, identity, version], separators=(",", ":")).encode()

    def encrypt(self, data: bytes, tenant: str, identity: str, version: str) -> bytes:
        nonce = secrets.token_bytes(12)
        return nonce + self.aes.encrypt(
            nonce, data, self.associated_data(tenant, identity, version)
        )

    def decrypt(self, data: bytes, tenant: str, identity: str, version: str) -> bytes:
        return self.aes.decrypt(
            data[:12], data[12:], self.associated_data(tenant, identity, version)
        )


class RateLimiter:
    """Bounded process-local limiter; deployment must use one API worker."""

    def __init__(self, capacity: int = 2048):
        self.capacity = capacity
        self.items: dict[str, tuple[float, int]] = {}
        self.lock = Lock()

    def allow(self, key: str, limit: int, seconds: float) -> bool:
        now = monotonic()
        with self.lock:
            self.items = {k: v for k, v in self.items.items() if v[0] > now}
            if key not in self.items and len(self.items) >= self.capacity:
                return False
            expires, count = self.items.get(key, (now + seconds, 0))
            self.items[key] = (expires, count + 1)
            return count < limit


def require_role(principal: Principal, *roles: str) -> None:
    if principal.role not in roles:
        raise AccessDenied()
