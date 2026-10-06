"""system settings

Revision ID: 0006_system_settings
Revises: 0005_audit_logs
Create Date: 2026-10-06
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision="0006_system_settings"
down_revision="0005_audit_logs"
branch_labels=None
depends_on=None

def upgrade():
    op.create_table(
        "system_settings",
        sa.Column("id",postgresql.UUID(as_uuid=True),primary_key=True,nullable=False),
        sa.Column("institution_name",sa.String(length=200),nullable=False),
        sa.Column("tax_id",sa.String(length=30),nullable=True),
        sa.Column("address",sa.Text(),nullable=True),
        sa.Column("phone",sa.String(length=40),nullable=True),
        sa.Column("email",sa.String(length=180),nullable=True),
        sa.Column("city",sa.String(length=100),nullable=False),
        sa.Column("province",sa.String(length=100),nullable=False),
        sa.Column("reservation_default_days",sa.Integer(),nullable=False),
        sa.Column("currency_symbol",sa.String(length=10),nullable=False),
        sa.Column("public_base_url",sa.String(length=500),nullable=False),
        sa.Column("document_footer",sa.String(length=255),nullable=False),
        sa.Column("timezone",sa.String(length=80),nullable=False),
        sa.Column("updated_at",sa.DateTime(timezone=True),nullable=False),
    )

def downgrade():
    op.drop_table("system_settings")
