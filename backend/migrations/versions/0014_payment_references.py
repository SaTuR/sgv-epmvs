"""payment references and bank receipt

Revision ID: 0014_payment_references
Revises: 0013_notification_center
Create Date: 2026-11-04
"""
from alembic import op
import sqlalchemy as sa

revision="0014_payment_references"
down_revision="0013_notification_center"
branch_labels=None
depends_on=None

def upgrade():
    op.add_column("sales",sa.Column("down_payment_date",sa.Date(),nullable=True))
    op.add_column("sales",sa.Column("down_payment_method",sa.String(length=30),nullable=True))
    op.add_column("sales",sa.Column("down_payment_reference",sa.String(length=120),nullable=True))
    op.add_column("sales",sa.Column("down_payment_bank_receipt",sa.String(length=120),nullable=True))
    op.add_column("payments",sa.Column("bank_receipt",sa.String(length=120),nullable=True))

def downgrade():
    op.drop_column("payments","bank_receipt")
    op.drop_column("sales","down_payment_bank_receipt")
    op.drop_column("sales","down_payment_reference")
    op.drop_column("sales","down_payment_method")
    op.drop_column("sales","down_payment_date")
