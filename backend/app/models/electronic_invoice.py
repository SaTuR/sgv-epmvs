import uuid
from datetime import date, datetime
from decimal import Decimal
from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.db import Base

class ElectronicInvoice(Base):
    __tablename__="electronic_invoices"

    id:Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),primary_key=True,default=uuid.uuid4)
    sale_id:Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),ForeignKey("sales.id",ondelete="RESTRICT"),unique=True,index=True)
    customer_id:Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),ForeignKey("customers.id",ondelete="RESTRICT"),index=True)
    property_id:Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),ForeignKey("properties.id",ondelete="RESTRICT"),index=True)
    issue_date:Mapped[date]=mapped_column(Date,default=date.today,index=True)
    environment:Mapped[str]=mapped_column(String(20),default="TEST")
    establishment_code:Mapped[str|None]=mapped_column(String(3),nullable=True)
    emission_point:Mapped[str|None]=mapped_column(String(3),nullable=True)
    sequential:Mapped[str|None]=mapped_column(String(9),nullable=True)
    document_number:Mapped[str|None]=mapped_column(String(17),nullable=True,unique=True)
    status:Mapped[str]=mapped_column(String(30),default="PENDING_CONFIG",index=True)
    total:Mapped[Decimal]=mapped_column(Numeric(14,2))
    access_key:Mapped[str|None]=mapped_column(String(49),nullable=True,unique=True)
    authorization_number:Mapped[str|None]=mapped_column(String(80),nullable=True)
    authorized_at:Mapped[datetime|None]=mapped_column(DateTime(timezone=True),nullable=True)
    xml_path:Mapped[str|None]=mapped_column(String(500),nullable=True)
    ride_path:Mapped[str|None]=mapped_column(String(500),nullable=True)
    error_message:Mapped[str|None]=mapped_column(Text,nullable=True)
    created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=datetime.utcnow)
    updated_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=datetime.utcnow,onupdate=datetime.utcnow)
