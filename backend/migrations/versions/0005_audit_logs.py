"""audit logs
Revision ID: 0005_audit_logs
Revises: 0004_issued_documents
Create Date: 2026-10-05
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision="0005_audit_logs"
down_revision="0004_issued_documents"
branch_labels=None
depends_on=None

def upgrade():
    op.create_table(
        "audit_logs",
        sa.Column("id",postgresql.UUID(as_uuid=True),primary_key=True),
        sa.Column("user_id",postgresql.UUID(as_uuid=True),sa.ForeignKey("users.id",ondelete="SET NULL"),nullable=True),
        sa.Column("user_email",sa.String(180),nullable=True),
        sa.Column("action",sa.String(120),nullable=False),
        sa.Column("target_type",sa.String(80),nullable=False),
        sa.Column("target_id",sa.String(120),nullable=True),
        sa.Column("ip_address",sa.String(64),nullable=True),
        sa.Column("details",sa.Text(),nullable=True),
        sa.Column("created_at",sa.DateTime(timezone=True),nullable=False),
    )
    op.create_index("ix_audit_logs_user_id","audit_logs",["user_id"])
    op.create_index("ix_audit_logs_user_email","audit_logs",["user_email"])
    op.create_index("ix_audit_logs_action","audit_logs",["action"])
    op.create_index("ix_audit_logs_target_type","audit_logs",["target_type"])
    op.create_index("ix_audit_logs_target_id","audit_logs",["target_id"])
    op.create_index("ix_audit_logs_created_at","audit_logs",["created_at"])

def downgrade():
    op.drop_table("audit_logs")
