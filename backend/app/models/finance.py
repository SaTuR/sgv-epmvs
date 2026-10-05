import uuid
from datetime import date, datetime
from decimal import Decimal
from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Numeric, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db import Base

class Reservation(Base):
    __tablename__="reservations"
    id:Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),primary_key=True,default=uuid.uuid4)
    customer_id:Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),ForeignKey("customers.id",ondelete="RESTRICT"),index=True)
    property_id:Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),ForeignKey("properties.id",ondelete="RESTRICT"),index=True)
    reservation_date:Mapped[date]=mapped_column(Date,default=date.today)
    expires_on:Mapped[date|None]=mapped_column(Date,nullable=True)
    notes:Mapped[str|None]=mapped_column(Text,nullable=True)
    active:Mapped[bool]=mapped_column(Boolean,default=True)
    created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=datetime.utcnow)

class Sale(Base):
    __tablename__="sales"
    id:Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),primary_key=True,default=uuid.uuid4)
    customer_id:Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),ForeignKey("customers.id",ondelete="RESTRICT"),index=True)
    property_id:Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),ForeignKey("properties.id",ondelete="RESTRICT"),unique=True,index=True)
    reservation_id:Mapped[uuid.UUID|None]=mapped_column(UUID(as_uuid=True),ForeignKey("reservations.id",ondelete="SET NULL"),nullable=True)
    confirmation_date:Mapped[date]=mapped_column(Date,default=date.today)
    sale_price:Mapped[Decimal]=mapped_column(Numeric(14,2))
    down_payment:Mapped[Decimal]=mapped_column(Numeric(14,2),default=0)
    financed_amount:Mapped[Decimal]=mapped_column(Numeric(14,2),default=0)
    installment_count:Mapped[int]=mapped_column(default=1)
    frequency:Mapped[str]=mapped_column(String(20),default="MONTHLY")
    first_due_date:Mapped[date]=mapped_column(Date)
    notes:Mapped[str|None]=mapped_column(Text,nullable=True)
    active:Mapped[bool]=mapped_column(Boolean,default=True)
    created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=datetime.utcnow)
    installments:Mapped[list["Installment"]]=relationship(back_populates="sale",cascade="all, delete-orphan")

class Installment(Base):
    __tablename__="installments"
    __table_args__=(UniqueConstraint("sale_id","number",name="uq_installment_sale_number"),)
    id:Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),primary_key=True,default=uuid.uuid4)
    sale_id:Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),ForeignKey("sales.id",ondelete="CASCADE"),index=True)
    number:Mapped[int]=mapped_column()
    due_date:Mapped[date]=mapped_column(Date,index=True)
    amount:Mapped[Decimal]=mapped_column(Numeric(14,2))
    paid_amount:Mapped[Decimal]=mapped_column(Numeric(14,2),default=0)
    status:Mapped[str]=mapped_column(String(20),default="PENDING",index=True)
    sale:Mapped[Sale]=relationship(back_populates="installments")

class Payment(Base):
    __tablename__="payments"
    id:Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),primary_key=True,default=uuid.uuid4)
    sale_id:Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),ForeignKey("sales.id",ondelete="RESTRICT"),index=True)
    payment_date:Mapped[date]=mapped_column(Date,default=date.today,index=True)
    amount:Mapped[Decimal]=mapped_column(Numeric(14,2))
    payment_method:Mapped[str]=mapped_column(String(30))
    reference:Mapped[str|None]=mapped_column(String(120),nullable=True)
    notes:Mapped[str|None]=mapped_column(Text,nullable=True)
    status:Mapped[str]=mapped_column(String(20),default="POSTED")
    created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=datetime.utcnow)
    allocations:Mapped[list["PaymentAllocation"]]=relationship(cascade="all, delete-orphan")

class PaymentAllocation(Base):
    __tablename__="payment_allocations"
    id:Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),primary_key=True,default=uuid.uuid4)
    payment_id:Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),ForeignKey("payments.id",ondelete="CASCADE"),index=True)
    installment_id:Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),ForeignKey("installments.id",ondelete="RESTRICT"),index=True)
    amount:Mapped[Decimal]=mapped_column(Numeric(14,2))

class PropertyMapZone(Base):
    __tablename__="property_map_zones"
    id:Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),primary_key=True,default=uuid.uuid4)
    stage_map_id:Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),ForeignKey("stage_maps.id",ondelete="CASCADE"),index=True)
    property_id:Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),ForeignKey("properties.id",ondelete="CASCADE"),unique=True,index=True)
    polygon_coordinates:Mapped[str]=mapped_column(Text)
    label_position:Mapped[str|None]=mapped_column(Text,nullable=True)
