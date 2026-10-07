"""SRI web services responses

Revision ID: 0010_sri_web_services
Revises: 0009_sri_signing_certificate
Create Date: 2026-10-07
"""
from alembic import op
import sqlalchemy as sa

revision="0010_sri_web_services"
down_revision="0009_sri_signing_certificate"
branch_labels=None
depends_on=None

def upgrade():
    op.add_column("electronic_invoices",sa.Column("sri_reception_response",sa.Text(),nullable=True))
    op.add_column("electronic_invoices",sa.Column("sri_authorization_response",sa.Text(),nullable=True))
    op.add_column("electronic_invoices",sa.Column("authorization_xml_path",sa.String(length=500),nullable=True))

def downgrade():
    op.drop_column("electronic_invoices","authorization_xml_path")
    op.drop_column("electronic_invoices","sri_authorization_response")
    op.drop_column("electronic_invoices","sri_reception_response")
