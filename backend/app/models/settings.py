import uuid
from datetime import datetime
from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.db import Base

class SystemSetting(Base):
    __tablename__="system_settings"

    id:Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),primary_key=True,default=uuid.uuid4)
    institution_name:Mapped[str]=mapped_column(String(200),default="Empresa Pública Municipal de Vivienda de Samborondón")
    tax_id:Mapped[str|None]=mapped_column(String(30),nullable=True)
    address:Mapped[str|None]=mapped_column(Text,nullable=True)
    phone:Mapped[str|None]=mapped_column(String(40),nullable=True)
    email:Mapped[str|None]=mapped_column(String(180),nullable=True)
    city:Mapped[str]=mapped_column(String(100),default="Samborondón")
    province:Mapped[str]=mapped_column(String(100),default="Guayas")
    reservation_default_days:Mapped[int]=mapped_column(Integer,default=3)
    currency_symbol:Mapped[str]=mapped_column(String(10),default="$")
    public_base_url:Mapped[str]=mapped_column(String(500),default="http://localhost:8080/api/public/documents")
    document_footer:Mapped[str]=mapped_column(String(255),default="Sistema de Gestión y Venta EPMVS")
    timezone:Mapped[str]=mapped_column(String(80),default="America/Guayaquil")
    updated_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=datetime.utcnow,onupdate=datetime.utcnow)
