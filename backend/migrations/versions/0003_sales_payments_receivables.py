"""sales payments receivables
Revision ID: 0003_sales_payments_receivables
Revises: 0002_customers_properties
Create Date: 2026-10-05
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision="0003_sales_payments_receivables"
down_revision="0002_customers_properties"
branch_labels=None
depends_on=None

def upgrade():
    op.create_table("reservations",
      sa.Column("id",postgresql.UUID(as_uuid=True),primary_key=True),
      sa.Column("customer_id",postgresql.UUID(as_uuid=True),sa.ForeignKey("customers.id",ondelete="RESTRICT"),nullable=False),
      sa.Column("property_id",postgresql.UUID(as_uuid=True),sa.ForeignKey("properties.id",ondelete="RESTRICT"),nullable=False),
      sa.Column("reservation_date",sa.Date(),nullable=False),sa.Column("expires_on",sa.Date()),sa.Column("notes",sa.Text()),
      sa.Column("active",sa.Boolean(),nullable=False,server_default=sa.true()),
      sa.Column("created_at",sa.DateTime(timezone=True),nullable=False))
    op.create_index("ix_reservations_customer_id","reservations",["customer_id"])
    op.create_index("ix_reservations_property_id","reservations",["property_id"])

    op.create_table("sales",
      sa.Column("id",postgresql.UUID(as_uuid=True),primary_key=True),
      sa.Column("customer_id",postgresql.UUID(as_uuid=True),sa.ForeignKey("customers.id",ondelete="RESTRICT"),nullable=False),
      sa.Column("property_id",postgresql.UUID(as_uuid=True),sa.ForeignKey("properties.id",ondelete="RESTRICT"),nullable=False),
      sa.Column("reservation_id",postgresql.UUID(as_uuid=True),sa.ForeignKey("reservations.id",ondelete="SET NULL")),
      sa.Column("confirmation_date",sa.Date(),nullable=False),sa.Column("sale_price",sa.Numeric(14,2),nullable=False),
      sa.Column("down_payment",sa.Numeric(14,2),nullable=False),sa.Column("financed_amount",sa.Numeric(14,2),nullable=False),
      sa.Column("installment_count",sa.Integer(),nullable=False),sa.Column("frequency",sa.String(20),nullable=False),
      sa.Column("first_due_date",sa.Date(),nullable=False),sa.Column("notes",sa.Text()),
      sa.Column("active",sa.Boolean(),nullable=False,server_default=sa.true()),
      sa.Column("created_at",sa.DateTime(timezone=True),nullable=False),
      sa.UniqueConstraint("property_id"))
    op.create_index("ix_sales_customer_id","sales",["customer_id"])
    op.create_index("ix_sales_property_id","sales",["property_id"],unique=True)

    op.create_table("installments",
      sa.Column("id",postgresql.UUID(as_uuid=True),primary_key=True),
      sa.Column("sale_id",postgresql.UUID(as_uuid=True),sa.ForeignKey("sales.id",ondelete="CASCADE"),nullable=False),
      sa.Column("number",sa.Integer(),nullable=False),sa.Column("due_date",sa.Date(),nullable=False),
      sa.Column("amount",sa.Numeric(14,2),nullable=False),sa.Column("paid_amount",sa.Numeric(14,2),nullable=False),
      sa.Column("status",sa.String(20),nullable=False),
      sa.UniqueConstraint("sale_id","number",name="uq_installment_sale_number"))
    op.create_index("ix_installments_sale_id","installments",["sale_id"])
    op.create_index("ix_installments_due_date","installments",["due_date"])
    op.create_index("ix_installments_status","installments",["status"])

    op.create_table("payments",
      sa.Column("id",postgresql.UUID(as_uuid=True),primary_key=True),
      sa.Column("sale_id",postgresql.UUID(as_uuid=True),sa.ForeignKey("sales.id",ondelete="RESTRICT"),nullable=False),
      sa.Column("payment_date",sa.Date(),nullable=False),sa.Column("amount",sa.Numeric(14,2),nullable=False),
      sa.Column("payment_method",sa.String(30),nullable=False),sa.Column("reference",sa.String(120)),
      sa.Column("notes",sa.Text()),sa.Column("status",sa.String(20),nullable=False),
      sa.Column("created_at",sa.DateTime(timezone=True),nullable=False))
    op.create_index("ix_payments_sale_id","payments",["sale_id"])
    op.create_index("ix_payments_payment_date","payments",["payment_date"])

    op.create_table("payment_allocations",
      sa.Column("id",postgresql.UUID(as_uuid=True),primary_key=True),
      sa.Column("payment_id",postgresql.UUID(as_uuid=True),sa.ForeignKey("payments.id",ondelete="CASCADE"),nullable=False),
      sa.Column("installment_id",postgresql.UUID(as_uuid=True),sa.ForeignKey("installments.id",ondelete="RESTRICT"),nullable=False),
      sa.Column("amount",sa.Numeric(14,2),nullable=False))
    op.create_index("ix_payment_allocations_payment_id","payment_allocations",["payment_id"])
    op.create_index("ix_payment_allocations_installment_id","payment_allocations",["installment_id"])

    op.create_table("property_map_zones",
      sa.Column("id",postgresql.UUID(as_uuid=True),primary_key=True),
      sa.Column("stage_map_id",postgresql.UUID(as_uuid=True),sa.ForeignKey("stage_maps.id",ondelete="CASCADE"),nullable=False),
      sa.Column("property_id",postgresql.UUID(as_uuid=True),sa.ForeignKey("properties.id",ondelete="CASCADE"),nullable=False),
      sa.Column("polygon_coordinates",sa.Text(),nullable=False),sa.Column("label_position",sa.Text()),
      sa.UniqueConstraint("property_id"))
    op.create_index("ix_property_map_zones_stage_map_id","property_map_zones",["stage_map_id"])
    op.create_index("ix_property_map_zones_property_id","property_map_zones",["property_id"],unique=True)

def downgrade():
    op.drop_table("property_map_zones")
    op.drop_table("payment_allocations")
    op.drop_table("payments")
    op.drop_table("installments")
    op.drop_table("sales")
    op.drop_table("reservations")
