"""Revocable device login grants; only token digests are persisted."""
import sqlalchemy as sa
from alembic import op

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table("remembered_logins",
        sa.Column("digest", sa.String(64), primary_key=True),
        sa.Column("tenant_id", sa.String(128), nullable=False),
        sa.Column("user_id", sa.String(128), nullable=False),
        sa.Column("password_version", sa.String(64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id", "user_id"],
                                ["memberships.tenant_id", "memberships.user_id"], ondelete="CASCADE"))
    op.create_index("ix_remembered_logins_tenant_id", "remembered_logins", ["tenant_id"])
    op.create_index("ix_remembered_logins_user_id", "remembered_logins", ["user_id"])


def downgrade():
    op.drop_table("remembered_logins")
