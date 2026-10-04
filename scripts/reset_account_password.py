"""Reset one existing organization account from the local backend container."""

import getpass
import re

from praxis.config import Settings
from praxis.db.models import Membership, User
from praxis.db.repository import Repository
from praxis.security import hash_password
from sqlalchemy import select


def main() -> None:
    tenant = input("Organization ID: ").strip()
    username = input("Username to reset: ").strip()
    if not re.fullmatch(r"[A-Za-z0-9_.:@-]{1,128}", tenant):
        raise ValueError("Invalid organization ID")
    if not re.fullmatch(r"[A-Za-z0-9_.:@-]{1,128}", username):
        raise ValueError("Invalid username")
    password = getpass.getpass("New password (at least 12 characters): ").rstrip("\r")
    confirmation = getpass.getpass("Confirm new password: ").rstrip("\r")
    if password != confirmation:
        raise ValueError("Passwords do not match")
    encoded = hash_password(password)
    repo = Repository.from_url(Settings().database_url.get_secret_value())
    try:
        with repo.sessions.begin() as db:
            user = db.scalar(
                select(User).join(Membership, Membership.user_id == User.id).where(
                    Membership.tenant_id == tenant, User.username == username
                )
            )
            if user is None:
                raise ValueError("Account was not found in that organization")
            user.password_hash = encoded
    finally:
        repo.engine.dispose()
    print("Password reset completed")


if __name__ == "__main__":
    main()
