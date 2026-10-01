"""Tenant-scoped dashboard labels and latest supplied-model metadata."""
import sqlalchemy as sa
from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("sessions", sa.Column("created_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("sessions", sa.Column("remote_name", sa.String(128), nullable=True))
    op.add_column("sessions", sa.Column("remote_number", sa.String(64), nullable=True))
    op.add_column("sessions", sa.Column("call_connected_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("sessions", sa.Column("latest_analysis", sa.JSON(), nullable=True))
    op.add_column("sessions", sa.Column("latest_analysis_at", sa.DateTime(timezone=True), nullable=True))
    # Historical rows retain their original timestamp in the locked SessionView payload.
    op.create_index("ix_sessions_tenant_created", "sessions", ["tenant_id", "created_at"])


def downgrade():
    op.drop_index("ix_sessions_tenant_created", table_name="sessions")
    for name in ("latest_analysis_at", "latest_analysis", "call_connected_at", "remote_number", "remote_name", "created_at"):
        op.drop_column("sessions", name)
