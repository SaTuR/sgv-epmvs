import uuid
from datetime import datetime
from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.db import Base

class NotificationSetting(Base):
    __tablename__="notification_settings"

    id:Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),primary_key=True,default=uuid.uuid4)
    whatsapp_enabled:Mapped[bool]=mapped_column(Boolean,default=False)
    whatsapp_phone_number_id:Mapped[str|None]=mapped_column(String(100),nullable=True)
    whatsapp_access_token_encrypted:Mapped[str|None]=mapped_column(Text,nullable=True)
    whatsapp_api_version:Mapped[str]=mapped_column(String(20),default="v24.0")

    sms_enabled:Mapped[bool]=mapped_column(Boolean,default=False)
    sms_provider:Mapped[str]=mapped_column(String(30),default="TWILIO")
    sms_account_sid:Mapped[str|None]=mapped_column(String(100),nullable=True)
    sms_auth_token_encrypted:Mapped[str|None]=mapped_column(Text,nullable=True)
    sms_from_number:Mapped[str|None]=mapped_column(String(40),nullable=True)

    email_enabled:Mapped[bool]=mapped_column(Boolean,default=False)
    updated_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=datetime.utcnow,onupdate=datetime.utcnow)

class NotificationTemplate(Base):
    __tablename__="notification_templates"
    __table_args__=(UniqueConstraint("event_type","channel",name="uq_notification_template_event_channel"),)

    id:Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),primary_key=True,default=uuid.uuid4)
    event_type:Mapped[str]=mapped_column(String(50),index=True)
    channel:Mapped[str]=mapped_column(String(20),index=True)
    name:Mapped[str]=mapped_column(String(120))
    subject:Mapped[str|None]=mapped_column(String(300),nullable=True)
    body:Mapped[str]=mapped_column(Text)
    active:Mapped[bool]=mapped_column(Boolean,default=True)
    created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=datetime.utcnow)
    updated_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=datetime.utcnow,onupdate=datetime.utcnow)

class NotificationLog(Base):
    __tablename__="notification_logs"

    id:Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),primary_key=True,default=uuid.uuid4)
    customer_id:Mapped[uuid.UUID|None]=mapped_column(UUID(as_uuid=True),ForeignKey("customers.id",ondelete="SET NULL"),nullable=True,index=True)
    sale_id:Mapped[uuid.UUID|None]=mapped_column(UUID(as_uuid=True),ForeignKey("sales.id",ondelete="SET NULL"),nullable=True,index=True)
    event_type:Mapped[str]=mapped_column(String(50),index=True)
    channel:Mapped[str]=mapped_column(String(20),index=True)
    recipient:Mapped[str]=mapped_column(String(255),index=True)
    subject:Mapped[str|None]=mapped_column(String(300),nullable=True)
    body:Mapped[str]=mapped_column(Text)
    status:Mapped[str]=mapped_column(String(30),default="PENDING",index=True)
    provider_message_id:Mapped[str|None]=mapped_column(String(255),nullable=True)
    error:Mapped[str|None]=mapped_column(Text,nullable=True)
    created_by:Mapped[uuid.UUID|None]=mapped_column(UUID(as_uuid=True),ForeignKey("users.id",ondelete="SET NULL"),nullable=True,index=True)
    created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=datetime.utcnow,index=True)
    sent_at:Mapped[datetime|None]=mapped_column(DateTime(timezone=True),nullable=True)
