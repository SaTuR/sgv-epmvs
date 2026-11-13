import uuid
from datetime import datetime
from decimal import Decimal
from sqlalchemy import Boolean, DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.db import Base

class Seller(Base):
    __tablename__="sellers"
    id:Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),primary_key=True,default=uuid.uuid4)
    identification:Mapped[str]=mapped_column(String(20),unique=True,index=True)
    first_name:Mapped[str]=mapped_column(String(100))
    last_name:Mapped[str]=mapped_column(String(100))
    phone:Mapped[str|None]=mapped_column(String(30),nullable=True)
    email:Mapped[str|None]=mapped_column(String(150),nullable=True)
    seller_type:Mapped[str]=mapped_column(String(20),default="INTERNAL")
    default_commission_rate:Mapped[Decimal]=mapped_column(Numeric(7,4),default=0)
    active:Mapped[bool]=mapped_column(Boolean,default=True)
    created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=datetime.utcnow)

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

class SaleCommission(Base):
    __tablename__="sale_commissions"
    id:Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),primary_key=True,default=uuid.uuid4)
    sale_id:Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),ForeignKey("sales.id",ondelete="CASCADE"),index=True)
    seller_id:Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),ForeignKey("sellers.id",ondelete="RESTRICT"),index=True)
    commission_base:Mapped[Decimal]=mapped_column(Numeric(14,2))
    commission_rate:Mapped[Decimal]=mapped_column(Numeric(7,4))
    commission_amount:Mapped[Decimal]=mapped_column(Numeric(14,2))
    status:Mapped[str]=mapped_column(String(20),default="PENDING",index=True)
    approved_at:Mapped[datetime|None]=mapped_column(DateTime(timezone=True),nullable=True)
    approved_by:Mapped[uuid.UUID|None]=mapped_column(UUID(as_uuid=True),ForeignKey("users.id",ondelete="SET NULL"),nullable=True)
    paid_at:Mapped[datetime|None]=mapped_column(DateTime(timezone=True),nullable=True)
    payment_reference:Mapped[str|None]=mapped_column(String(120),nullable=True)
    notes:Mapped[str|None]=mapped_column(Text,nullable=True)
    created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=datetime.utcnow)
