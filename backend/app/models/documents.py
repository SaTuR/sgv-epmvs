import uuid
from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.db import Base

class IssuedDocument(Base):
    __tablename__="issued_documents"

    id:Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),primary_key=True,default=uuid.uuid4)
    document_type:Mapped[str]=mapped_column(String(40),index=True)
    document_number:Mapped[str]=mapped_column(String(40),unique=True,index=True)
    verification_code:Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),unique=True,index=True,default=uuid.uuid4)
    sale_id:Mapped[uuid.UUID|None]=mapped_column(UUID(as_uuid=True),ForeignKey("sales.id",ondelete="CASCADE"),nullable=True,index=True)
    payment_id:Mapped[uuid.UUID|None]=mapped_column(UUID(as_uuid=True),ForeignKey("payments.id",ondelete="CASCADE"),nullable=True,index=True)
    created_by:Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),ForeignKey("users.id",ondelete="RESTRICT"),index=True)
    created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=datetime.utcnow)
