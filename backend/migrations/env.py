import os
from alembic import context
from sqlalchemy import create_engine, pool
from praxis.db.models import Base

url = os.environ["PRAXIS_MIGRATION_DATABASE_URL"]
if not url.startswith("postgresql+psycopg://"):
    raise ValueError("PostgreSQL migration URL required")
if context.is_offline_mode():
    context.configure(
        url=url,
        target_metadata=Base.metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()
else:
    engine = create_engine(url, poolclass=pool.NullPool, hide_parameters=True)
    with engine.connect() as connection:
        context.configure(connection=connection, target_metadata=Base.metadata)
        with context.begin_transaction():
            context.run_migrations()
    engine.dispose()
