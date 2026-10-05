"""issued documents and numbering
Revision ID: 0004_issued_documents
Revises: 0003_sales_payments_receivables
Create Date: 2026-10-05
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision="0004_issued_documents"
down_revision="0003_sales_payments_receivables"
branch_labels=None
depends_on=None

def upgrade():
    op.execute("CREATE SEQUENCE IF NOT EXISTS sgv_document_number_seq START WITH 1 INCREMENT BY 1")
    op.create_table(
        "issued_documents",
        sa.Column("id",postgresql.UUID(as_uuid=True),primary_key=True),
        sa.Column("document_type",sa.String(40),nullable=False),
        sa.Column("document_number",sa.String(40),nullable=False),
        sa.Column("verification_code",postgresql.UUID(as_uuid=True),nullable=False),
        sa.Column("sale_id",postgresql.UUID(as_uuid=True),sa.ForeignKey("sales.id",ondelete="CASCADE"),nullable=True),
        sa.Column("payment_id",postgresql.UUID(as_uuid=True),sa.ForeignKey("payments.id",ondelete="CASCADE"),nullable=True),
        sa.Column("created_by",postgresql.UUID(as_uuid=True),sa.ForeignKey("users.id",ondelete="RESTRICT"),nullable=False),
        sa.Column("created_at",sa.DateTime(timezone=True),nullable=False),
        sa.UniqueConstraint("document_number"),
        sa.UniqueConstraint("verification_code"),
    )
    op.create_index("ix_issued_documents_document_type","issued_documents",["document_type"])
    op.create_index("ix_issued_documents_document_number","issued_documents",["document_number"],unique=True)
    op.create_index("ix_issued_documents_verification_code","issued_documents",["verification_code"],unique=True)
    op.create_index("ix_issued_documents_sale_id","issued_documents",["sale_id"])
    op.create_index("ix_issued_documents_payment_id","issued_documents",["payment_id"])
    op.create_index("ix_issued_documents_created_by","issued_documents",["created_by"])

def downgrade():
    op.drop_table("issued_documents")
    op.execute("DROP SEQUENCE IF EXISTS sgv_document_number_seq")
