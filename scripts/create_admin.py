"""Explicit local operator bootstrap, no default/demo account or password."""
import getpass
from uuid import uuid4

from praxis.config import Settings
from praxis.db.models import Membership, Organization, User
from praxis.db.repository import Repository
from praxis.security import hash_password

settings = Settings()
tenant = input("Organization ID: ").strip()
name = input("Organization name: ").strip()
username = input("Administrator username: ").strip()
password = getpass.getpass("New password (at least 12 characters): ")
from praxis.contracts.base import Identifier
from pydantic import TypeAdapter
TypeAdapter(Identifier).validate_python(tenant)
if not name or len(name)>256 or not username or len(username)>128:
    raise ValueError("Invalid organization name or username")
repo = Repository.from_url(settings.database_url.get_secret_value())
with repo.sessions.begin() as db:
    if db.get(Organization, tenant) is not None:
        raise ValueError("Organization already exists; use the existing administrator workflow")
    db.add(Organization(id=tenant, name=name))
    db.flush()
    uid = str(uuid4())
    db.add(User(id=uid, username=username, password_hash=hash_password(password), active=True))
    db.flush()
    db.add(Membership(tenant_id=tenant, user_id=uid, role="admin"))
repo.engine.dispose()
print("Organization administrator created")
