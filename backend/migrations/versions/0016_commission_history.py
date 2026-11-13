"""allow commission history per sale

Revision ID: 0016_commission_history
Revises: 0015_sellers_commissions
Create Date: 2026-11-13
"""
from alembic import op

revision="0016_commission_history"
down_revision="0015_sellers_commissions"
branch_labels=None
depends_on=None

def upgrade():
    op.execute("ALTER TABLE sale_commissions DROP CONSTRAINT IF EXISTS sale_commissions_sale_id_key")
    op.create_index("ix_sale_commissions_sale_id","sale_commissions",["sale_id"],unique=False)

def downgrade():
    op.drop_index("ix_sale_commissions_sale_id",table_name="sale_commissions")
    op.create_unique_constraint("sale_commissions_sale_id_key","sale_commissions",["sale_id"])
