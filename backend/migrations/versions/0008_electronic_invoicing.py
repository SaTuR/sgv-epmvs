"""electronic invoicing foundation

Revision ID: 0008_electronic_invoicing
Revises: 0007_backup_settings
Create Date: 2026-10-06
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision="0008_electronic_invoicing"
down_revision="0007_backup_settings"
branch_labels=None
depends_on=None

def upgrade():
    op.add_column("system_settings",sa.Column("sri_enabled",sa.Boolean(),nullable=False,server_default=sa.false()))
    op.add_column("system_settings",sa.Column("sri_environment",sa.String(length=20),nullable=False,server_default="TEST"))
    op.add_column("system_settings",sa.Column("sri_ruc",sa.String(length=13),nullable=True))
    op.add_column("system_settings",sa.Column("sri_business_name",sa.String(length=300),nullable=True))
    op.add_column("system_settings",sa.Column("sri_trade_name",sa.String(length=300),nullable=True))
    op.add_column("system_settings",sa.Column("sri_accounting_required",sa.Boolean(),nullable=False,server_default=sa.true()))
    op.add_column("system_settings",sa.Column("sri_special_taxpayer_code",sa.String(length=30),nullable=True))
    op.add_column("system_settings",sa.Column("sri_withholding_agent_code",sa.String(length=30),nullable=True))
    op.add_column("system_settings",sa.Column("sri_establishment_code",sa.String(length=3),nullable=True))
    op.add_column("system_settings",sa.Column("sri_emission_point",sa.String(length=3),nullable=True))
    op.add_column("system_settings",sa.Column("sri_invoice_sequence",sa.Integer(),nullable=False,server_default="1"))

    op.create_table(
        "electronic_invoices",
        sa.Column("id",postgresql.UUID(as_uuid=True),primary_key=True,nullable=False),
        sa.Column("sale_id",postgresql.UUID(as_uuid=True),sa.ForeignKey("sales.id",ondelete="RESTRICT"),nullable=False),
        sa.Column("customer_id",postgresql.UUID(as_uuid=True),sa.ForeignKey("customers.id",ondelete="RESTRICT"),nullable=False),
        sa.Column("property_id",postgresql.UUID(as_uuid=True),sa.ForeignKey("properties.id",ondelete="RESTRICT"),nullable=False),
        sa.Column("issue_date",sa.Date(),nullable=False),
        sa.Column("environment",sa.String(length=20),nullable=False),
        sa.Column("establishment_code",sa.String(length=3),nullable=True),
        sa.Column("emission_point",sa.String(length=3),nullable=True),
        sa.Column("sequential",sa.String(length=9),nullable=True),
        sa.Column("document_number",sa.String(length=17),nullable=True),
        sa.Column("status",sa.String(length=30),nullable=False),
        sa.Column("total",sa.Numeric(14,2),nullable=False),
        sa.Column("access_key",sa.String(length=49),nullable=True),
        sa.Column("authorization_number",sa.String(length=80),nullable=True),
        sa.Column("authorized_at",sa.DateTime(timezone=True),nullable=True),
        sa.Column("xml_path",sa.String(length=500),nullable=True),
        sa.Column("ride_path",sa.String(length=500),nullable=True),
        sa.Column("error_message",sa.Text(),nullable=True),
        sa.Column("created_at",sa.DateTime(timezone=True),nullable=False),
        sa.Column("updated_at",sa.DateTime(timezone=True),nullable=False),
        sa.UniqueConstraint("sale_id",name="uq_electronic_invoice_sale"),
        sa.UniqueConstraint("document_number",name="uq_electronic_invoice_number"),
        sa.UniqueConstraint("access_key",name="uq_electronic_invoice_access_key"),
    )
    op.create_index("ix_electronic_invoices_sale_id","electronic_invoices",["sale_id"])
    op.create_index("ix_electronic_invoices_customer_id","electronic_invoices",["customer_id"])
    op.create_index("ix_electronic_invoices_property_id","electronic_invoices",["property_id"])
    op.create_index("ix_electronic_invoices_issue_date","electronic_invoices",["issue_date"])
    op.create_index("ix_electronic_invoices_status","electronic_invoices",["status"])

def downgrade():
    op.drop_table("electronic_invoices")
    for name in [
        "sri_invoice_sequence","sri_emission_point","sri_establishment_code",
        "sri_withholding_agent_code","sri_special_taxpayer_code","sri_accounting_required",
        "sri_trade_name","sri_business_name","sri_ruc","sri_environment","sri_enabled"
    ]:
        op.drop_column("system_settings",name)
