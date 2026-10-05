import base64
import secrets

import pytest
from praxis.config import Settings
from praxis.db.models import Base, Membership, Organization, User
from praxis.db.repository import Repository
from praxis.security import hash_password
from sqlalchemy import create_engine, event
from sqlalchemy.pool import StaticPool


@pytest.fixture
def settings():
    return Settings(
        database_url="postgresql+psycopg://test:test@localhost/test",
        jwt_secret=secrets.token_urlsafe(48),
        embedding_key_base64=base64.b64encode(secrets.token_bytes(32)).decode(),
        _env_file=None,
        models_enabled=False,
    )


@pytest.fixture
def repo():
    # SQLite is an isolated repository/unit fixture, not a PostgreSQL integration claim.
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )

    @event.listens_for(engine, "connect")
    def enable_fk(connection, record):
        connection.execute("PRAGMA foreign_keys=ON")

    Base.metadata.create_all(engine)
    repo = Repository(engine)
    hashed = hash_password("test-password-only")
    with repo.sessions.begin() as db:
        for tenant in ["a", "b"]:
            db.add(Organization(id=tenant, name=tenant))
        db.flush()
        for uid, tenant, role in [
            ("admin-a", "a", "admin"),
            ("host-a", "a", "host"),
            ("analyst-a", "a", "analyst"),
            ("admin-b", "b", "admin"),
        ]:
            db.add(User(id=uid, username=uid, password_hash=hashed, active=True))
            db.flush()
            db.add(Membership(tenant_id=tenant, user_id=uid, role=role))
    yield repo
    engine.dispose()
