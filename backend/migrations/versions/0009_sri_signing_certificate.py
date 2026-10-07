"""SRI signing certificate

Revision ID: 0009_sri_signing_certificate
Revises: 0008_electronic_invoicing
Create Date: 2026-10-07
"""
from alembic import op
import sqlalchemy as sa

revision="0009_sri_signing_certificate"
down_revision="0008_electronic_invoicing"
branch_labels=None
depends_on=None

def upgrade():
    op.add_column("system_settings",sa.Column("sri_certificate_path",sa.String(length=500),nullable=True))
    op.add_column("system_settings",sa.Column("sri_certificate_password_encrypted",sa.Text(),nullable=True))
    op.add_column("system_settings",sa.Column("sri_certificate_subject",sa.String(length=500),nullable=True))
    op.add_column("system_settings",sa.Column("sri_certificate_issuer",sa.String(length=500),nullable=True))
    op.add_column("system_settings",sa.Column("sri_certificate_serial",sa.String(length=160),nullable=True))
    op.add_column("system_settings",sa.Column("sri_certificate_valid_from",sa.DateTime(timezone=True),nullable=True))
    op.add_column("system_settings",sa.Column("sri_certificate_valid_to",sa.DateTime(timezone=True),nullable=True))

def downgrade():
    for name in [
        "sri_certificate_valid_to","sri_certificate_valid_from","sri_certificate_serial",
        "sri_certificate_issuer","sri_certificate_subject",
        "sri_certificate_password_encrypted","sri_certificate_path"
    ]:
        op.drop_column("system_settings",name)
