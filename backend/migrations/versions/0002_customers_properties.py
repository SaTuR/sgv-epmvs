"""customers properties and stage maps
Revision ID: 0002_customers_properties
Revises: 0001_security_projects
Create Date: 2026-10-05
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision="0002_customers_properties"
down_revision="0001_security_projects"
branch_labels=None
depends_on=None

def upgrade():
    op.create_table("customers",
      sa.Column("id",postgresql.UUID(as_uuid=True),primary_key=True),
      sa.Column("identification_type",sa.String(20),nullable=False),sa.Column("identification",sa.String(30),nullable=False),
      sa.Column("first_name",sa.String(120),nullable=False),sa.Column("last_name",sa.String(120),nullable=False),
      sa.Column("birth_date",sa.Date()),sa.Column("marital_status",sa.String(40)),sa.Column("phone",sa.String(30)),
      sa.Column("mobile",sa.String(30)),sa.Column("email",sa.String(180)),sa.Column("address",sa.Text()),
      sa.Column("canton",sa.String(100)),sa.Column("province",sa.String(100)),sa.Column("notes",sa.Text()),
      sa.Column("active",sa.Boolean(),nullable=False,server_default=sa.true()),
      sa.Column("created_at",sa.DateTime(timezone=True),nullable=False),sa.UniqueConstraint("identification"))
    op.create_index("ix_customers_identification","customers",["identification"],unique=True)
    op.create_table("stage_maps",
      sa.Column("id",postgresql.UUID(as_uuid=True),primary_key=True),
      sa.Column("stage_id",postgresql.UUID(as_uuid=True),sa.ForeignKey("project_stages.id",ondelete="CASCADE"),nullable=False),
      sa.Column("name",sa.String(160),nullable=False),sa.Column("file_path",sa.String(500),nullable=False),
      sa.Column("file_type",sa.String(50),nullable=False),sa.Column("version",sa.Integer(),nullable=False),
      sa.Column("is_active",sa.Boolean(),nullable=False,server_default=sa.true()),
      sa.Column("created_at",sa.DateTime(timezone=True),nullable=False))
    op.create_index("ix_stage_maps_stage_id","stage_maps",["stage_id"])
    op.create_table("blocks",
      sa.Column("id",postgresql.UUID(as_uuid=True),primary_key=True),
      sa.Column("stage_id",postgresql.UUID(as_uuid=True),sa.ForeignKey("project_stages.id",ondelete="CASCADE"),nullable=False),
      sa.Column("name",sa.String(80),nullable=False),sa.Column("description",sa.String(255)),
      sa.Column("active",sa.Boolean(),nullable=False,server_default=sa.true()),
      sa.UniqueConstraint("stage_id","name",name="uq_block_stage_name"))
    op.create_index("ix_blocks_stage_id","blocks",["stage_id"])
    op.create_table("property_statuses",
      sa.Column("id",postgresql.UUID(as_uuid=True),primary_key=True),
      sa.Column("code",sa.String(40),nullable=False),sa.Column("name",sa.String(80),nullable=False),
      sa.Column("sort_order",sa.Integer(),nullable=False),sa.Column("active",sa.Boolean(),nullable=False,server_default=sa.true()),
      sa.UniqueConstraint("code"),sa.UniqueConstraint("name"))
    op.create_index("ix_property_statuses_code","property_statuses",["code"],unique=True)
    op.create_table("properties",
      sa.Column("id",postgresql.UUID(as_uuid=True),primary_key=True),
      sa.Column("block_id",postgresql.UUID(as_uuid=True),sa.ForeignKey("blocks.id",ondelete="RESTRICT"),nullable=False),
      sa.Column("status_id",postgresql.UUID(as_uuid=True),sa.ForeignKey("property_statuses.id",ondelete="RESTRICT"),nullable=False),
      sa.Column("code",sa.String(80),nullable=False),sa.Column("lot_number",sa.String(40),nullable=False),
      sa.Column("cadastral_key",sa.String(100)),sa.Column("area_m2",sa.Numeric(12,2),nullable=False),
      sa.Column("price_per_m2",sa.Numeric(14,4)),sa.Column("total_price",sa.Numeric(14,2),nullable=False),
      sa.Column("location_reference",sa.Text()),sa.Column("notes",sa.Text()),
      sa.Column("active",sa.Boolean(),nullable=False,server_default=sa.true()),
      sa.Column("created_at",sa.DateTime(timezone=True),nullable=False),
      sa.UniqueConstraint("block_id","lot_number",name="uq_property_block_lot"),sa.UniqueConstraint("code"))
    op.create_index("ix_properties_block_id","properties",["block_id"])
    op.create_index("ix_properties_status_id","properties",["status_id"])
    op.create_index("ix_properties_code","properties",["code"],unique=True)

def downgrade():
    op.drop_table("properties"); op.drop_table("property_statuses"); op.drop_table("blocks"); op.drop_table("stage_maps"); op.drop_table("customers")
