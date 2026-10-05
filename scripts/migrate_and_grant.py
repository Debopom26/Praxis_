"""Migration owner performs DDL; the runtime role receives only application DML."""
import os
from pathlib import Path

import psycopg
from psycopg import sql
from alembic import command
from alembic.config import Config

root = Path(__file__).resolve().parents[1]
command.upgrade(Config(str(root / "backend/alembic.ini")), "head")
url = os.environ["PRAXIS_MIGRATION_DATABASE_URL"].replace("postgresql+psycopg://", "postgresql://", 1)
password = os.environ["PRAXIS_RUNTIME_PASSWORD"]
with psycopg.connect(url) as connection:
    exists = connection.execute("SELECT 1 FROM pg_roles WHERE rolname='praxis_runtime'").fetchone()
    operation = "ALTER ROLE" if exists else "CREATE ROLE"
    connection.execute(sql.SQL(operation + " {} LOGIN PASSWORD {}").format(sql.Identifier("praxis_runtime"), sql.Literal(password)))
    database = connection.execute("SELECT current_database()").fetchone()[0]
    # PostgreSQL grants TEMP to PUBLIC by default; application DML needs no
    # temporary schemas. Database access is explicit for the runtime role.
    connection.execute(sql.SQL("REVOKE ALL ON DATABASE {} FROM PUBLIC").format(sql.Identifier(database)))
    connection.execute(sql.SQL("GRANT CONNECT ON DATABASE {} TO praxis_runtime").format(sql.Identifier(database)))
    connection.execute("REVOKE CREATE ON SCHEMA public FROM PUBLIC")
    connection.execute("GRANT USAGE ON SCHEMA public TO praxis_runtime")
    connection.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO praxis_runtime")
    connection.execute("GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO praxis_runtime")
    connection.execute("REVOKE ALL ON alembic_version FROM praxis_runtime")
print("Migrations and least-privilege runtime grants completed")
