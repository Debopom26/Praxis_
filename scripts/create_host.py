"""Interactive local operator command to add a second Praxis calling account."""

import getpass
import re
from uuid import uuid4

from praxis.config import Settings
from praxis.db.models import Membership, Organization, User
from praxis.db.repository import Repository
from praxis.security import hash_password
from sqlalchemy import select


def main() -> None:
    tenant = input("Existing organization ID: ").strip()
    username = input("New Praxis caller username: ").strip()
    password = getpass.getpass("New password (at least 12 characters): ").rstrip("\r")
    if not re.fullmatch(r"[A-Za-z0-9_.:@-]{1,128}", tenant):
        raise ValueError("Invalid organization ID")
    if not re.fullmatch(r"[A-Za-z0-9_.:@-]{1,128}", username):
        raise ValueError("Invalid username")
    encoded = hash_password(password)
    repo = Repository.from_url(Settings().database_url.get_secret_value())
    try:
        with repo.sessions.begin() as db:
            if db.get(Organization, tenant) is None:
                raise ValueError("Organization does not exist")
            if db.scalar(select(User.id).where(User.username == username)) is not None:
                raise ValueError("Username already exists")
            user_id = str(uuid4())
            db.add(User(id=user_id, username=username, password_hash=encoded, active=True))
            db.flush()
            db.add(Membership(tenant_id=tenant, user_id=user_id, role="host"))
    finally:
        repo.engine.dispose()
    print("Praxis caller account created")


if __name__ == "__main__":
    main()
