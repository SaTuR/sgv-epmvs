import uuid
from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.db import Base

class AuditLog(Base):
    __tablename__="audit_logs"

    id:Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),primary_key=True,default=uuid.uuid4)
    user_id:Mapped[uuid.UUID|None]=mapped_column(UUID(as_uuid=True),ForeignKey("users.id",ondelete="SET NULL"),nullable=True,index=True)
    user_email:Mapped[str|None]=mapped_column(String(180),nullable=True,index=True)
    action:Mapped[str]=mapped_column(String(120),index=True)
    target_type:Mapped[str]=mapped_column(String(80),index=True)
    target_id:Mapped[str|None]=mapped_column(String(120),nullable=True,index=True)
    ip_address:Mapped[str|None]=mapped_column(String(64),nullable=True)
    details:Mapped[str|None]=mapped_column(Text,nullable=True)
    created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=datetime.utcnow,index=True)
