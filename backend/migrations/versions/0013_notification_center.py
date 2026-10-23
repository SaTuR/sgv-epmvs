"""Notification center

Revision ID: 0013_notification_center
Revises: 0012_ride_layout
Create Date: 2026-10-22
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision="0013_notification_center"
down_revision="0012_ride_layout"
branch_labels=None
depends_on=None

def upgrade():
    op.create_table(
        "notification_settings",
        sa.Column("id",postgresql.UUID(as_uuid=True),primary_key=True),
        sa.Column("whatsapp_enabled",sa.Boolean(),nullable=False,server_default=sa.false()),
        sa.Column("whatsapp_phone_number_id",sa.String(length=100),nullable=True),
        sa.Column("whatsapp_access_token_encrypted",sa.Text(),nullable=True),
        sa.Column("whatsapp_api_version",sa.String(length=20),nullable=False,server_default="v24.0"),
        sa.Column("sms_enabled",sa.Boolean(),nullable=False,server_default=sa.false()),
        sa.Column("sms_provider",sa.String(length=30),nullable=False,server_default="TWILIO"),
        sa.Column("sms_account_sid",sa.String(length=100),nullable=True),
        sa.Column("sms_auth_token_encrypted",sa.Text(),nullable=True),
        sa.Column("sms_from_number",sa.String(length=40),nullable=True),
        sa.Column("email_enabled",sa.Boolean(),nullable=False,server_default=sa.false()),
        sa.Column("updated_at",sa.DateTime(timezone=True),nullable=False,server_default=sa.func.now()),
    )
    op.create_table(
        "notification_templates",
        sa.Column("id",postgresql.UUID(as_uuid=True),primary_key=True),
        sa.Column("event_type",sa.String(length=50),nullable=False),
        sa.Column("channel",sa.String(length=20),nullable=False),
        sa.Column("name",sa.String(length=120),nullable=False),
        sa.Column("subject",sa.String(length=300),nullable=True),
        sa.Column("body",sa.Text(),nullable=False),
        sa.Column("active",sa.Boolean(),nullable=False,server_default=sa.true()),
        sa.Column("created_at",sa.DateTime(timezone=True),nullable=False,server_default=sa.func.now()),
        sa.Column("updated_at",sa.DateTime(timezone=True),nullable=False,server_default=sa.func.now()),
        sa.UniqueConstraint("event_type","channel",name="uq_notification_template_event_channel"),
    )
    op.create_index("ix_notification_templates_event_type","notification_templates",["event_type"])
    op.create_index("ix_notification_templates_channel","notification_templates",["channel"])
    op.create_table(
        "notification_logs",
        sa.Column("id",postgresql.UUID(as_uuid=True),primary_key=True),
        sa.Column("customer_id",postgresql.UUID(as_uuid=True),sa.ForeignKey("customers.id",ondelete="SET NULL"),nullable=True),
        sa.Column("sale_id",postgresql.UUID(as_uuid=True),sa.ForeignKey("sales.id",ondelete="SET NULL"),nullable=True),
        sa.Column("event_type",sa.String(length=50),nullable=False),
        sa.Column("channel",sa.String(length=20),nullable=False),
        sa.Column("recipient",sa.String(length=255),nullable=False),
        sa.Column("subject",sa.String(length=300),nullable=True),
        sa.Column("body",sa.Text(),nullable=False),
        sa.Column("status",sa.String(length=30),nullable=False,server_default="PENDING"),
        sa.Column("provider_message_id",sa.String(length=255),nullable=True),
        sa.Column("error",sa.Text(),nullable=True),
        sa.Column("created_by",postgresql.UUID(as_uuid=True),sa.ForeignKey("users.id",ondelete="SET NULL"),nullable=True),
        sa.Column("created_at",sa.DateTime(timezone=True),nullable=False,server_default=sa.func.now()),
        sa.Column("sent_at",sa.DateTime(timezone=True),nullable=True),
    )
    for name,col in [
        ("ix_notification_logs_customer_id","customer_id"),
        ("ix_notification_logs_sale_id","sale_id"),
        ("ix_notification_logs_event_type","event_type"),
        ("ix_notification_logs_channel","channel"),
        ("ix_notification_logs_recipient","recipient"),
        ("ix_notification_logs_status","status"),
        ("ix_notification_logs_created_by","created_by"),
        ("ix_notification_logs_created_at","created_at"),
    ]:
        op.create_index(name,"notification_logs",[col])

def downgrade():
    op.drop_table("notification_logs")
    op.drop_table("notification_templates")
    op.drop_table("notification_settings")
