"""RIDE visual layout settings

Revision ID: 0012_ride_layout
Revises: 0011_ride_email_settings
Create Date: 2026-10-07
"""
from alembic import op
import sqlalchemy as sa

revision="0012_ride_layout"
down_revision="0011_ride_email_settings"
branch_labels=None
depends_on=None

def upgrade():
    op.add_column("system_settings",sa.Column("ride_code_type",sa.String(length=20),nullable=False,server_default="BARCODE"))
    op.add_column("system_settings",sa.Column("ride_barcode_height_mm",sa.Integer(),nullable=False,server_default="18"))
    op.add_column("system_settings",sa.Column("ride_show_payment_table",sa.Boolean(),nullable=False,server_default=sa.true()))
    op.add_column("system_settings",sa.Column("ride_show_additional_info",sa.Boolean(),nullable=False,server_default=sa.true()))

def downgrade():
    op.drop_column("system_settings","ride_show_additional_info")
    op.drop_column("system_settings","ride_show_payment_table")
    op.drop_column("system_settings","ride_barcode_height_mm")
    op.drop_column("system_settings","ride_code_type")
