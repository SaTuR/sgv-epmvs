"""sellers and sales commissions

Revision ID: 0015_sellers_commissions
Revises: 0014_payment_references
Create Date: 2026-11-12
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision="0015_sellers_commissions"
down_revision="0014_payment_references"
branch_labels=None
depends_on=None

def upgrade():
    op.create_table(
        "sellers",
        sa.Column("id",postgresql.UUID(as_uuid=True),primary_key=True),
        sa.Column("identification",sa.String(length=20),nullable=False,unique=True),
        sa.Column("first_name",sa.String(length=100),nullable=False),
        sa.Column("last_name",sa.String(length=100),nullable=False),
        sa.Column("phone",sa.String(length=30),nullable=True),
        sa.Column("email",sa.String(length=150),nullable=True),
        sa.Column("seller_type",sa.String(length=20),nullable=False,server_default="INTERNAL"),
        sa.Column("default_commission_rate",sa.Numeric(7,4),nullable=False,server_default="0"),
        sa.Column("active",sa.Boolean(),nullable=False,server_default=sa.true()),
        sa.Column("created_at",sa.DateTime(timezone=True),nullable=False),
    )
    op.add_column("sales",sa.Column("seller_id",postgresql.UUID(as_uuid=True),nullable=True))
    op.create_foreign_key("fk_sales_seller","sales","sellers",["seller_id"],["id"],ondelete="RESTRICT")
    op.create_index("ix_sales_seller_id","sales",["seller_id"])

    op.create_table(
        "sale_commissions",
        sa.Column("id",postgresql.UUID(as_uuid=True),primary_key=True),
        sa.Column("sale_id",postgresql.UUID(as_uuid=True),nullable=False,unique=True),
        sa.Column("seller_id",postgresql.UUID(as_uuid=True),nullable=False),
        sa.Column("commission_base",sa.Numeric(14,2),nullable=False),
        sa.Column("commission_rate",sa.Numeric(7,4),nullable=False),
        sa.Column("commission_amount",sa.Numeric(14,2),nullable=False),
        sa.Column("status",sa.String(length=20),nullable=False,server_default="PENDING"),
        sa.Column("approved_at",sa.DateTime(timezone=True),nullable=True),
        sa.Column("approved_by",postgresql.UUID(as_uuid=True),nullable=True),
        sa.Column("paid_at",sa.DateTime(timezone=True),nullable=True),
        sa.Column("payment_reference",sa.String(length=120),nullable=True),
        sa.Column("notes",sa.Text(),nullable=True),
        sa.Column("created_at",sa.DateTime(timezone=True),nullable=False),
        sa.ForeignKeyConstraint(["sale_id"],["sales.id"],ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["seller_id"],["sellers.id"],ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["approved_by"],["users.id"],ondelete="SET NULL"),
    )
    op.create_index("ix_sale_commissions_seller_id","sale_commissions",["seller_id"])
    op.create_index("ix_sale_commissions_status","sale_commissions",["status"])

def downgrade():
    op.drop_index("ix_sale_commissions_status",table_name="sale_commissions")
    op.drop_index("ix_sale_commissions_seller_id",table_name="sale_commissions")
    op.drop_table("sale_commissions")
    op.drop_index("ix_sales_seller_id",table_name="sales")
    op.drop_constraint("fk_sales_seller","sales",type_="foreignkey")
    op.drop_column("sales","seller_id")
    op.drop_table("sellers")
