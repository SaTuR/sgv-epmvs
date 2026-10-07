import uuid
from datetime import datetime
from sqlalchemy import Boolean, DateTime, Integer, String, Text
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
    backup_enabled:Mapped[bool]=mapped_column(Boolean,default=False)
    backup_provider:Mapped[str]=mapped_column(String(20),default="GDRIVE")
    backup_remote_name:Mapped[str]=mapped_column(String(120),default="")
    backup_folder:Mapped[str]=mapped_column(String(255),default="SGV-EPMVS/backups")
    backup_time:Mapped[str]=mapped_column(String(5),default="02:00")
    backup_keep_last:Mapped[int]=mapped_column(Integer,default=2)
    backup_run_requested:Mapped[bool]=mapped_column(Boolean,default=False)
    backup_last_run:Mapped[datetime|None]=mapped_column(DateTime(timezone=True),nullable=True)
    backup_last_status:Mapped[str]=mapped_column(String(20),default="NEVER")
    backup_last_filename:Mapped[str|None]=mapped_column(String(255),nullable=True)
    backup_last_error:Mapped[str|None]=mapped_column(Text,nullable=True)
    sri_enabled:Mapped[bool]=mapped_column(Boolean,default=False)
    sri_environment:Mapped[str]=mapped_column(String(20),default="TEST")
    sri_ruc:Mapped[str|None]=mapped_column(String(13),nullable=True)
    sri_business_name:Mapped[str|None]=mapped_column(String(300),nullable=True)
    sri_trade_name:Mapped[str|None]=mapped_column(String(300),nullable=True)
    sri_accounting_required:Mapped[bool]=mapped_column(Boolean,default=True)
    sri_special_taxpayer_code:Mapped[str|None]=mapped_column(String(30),nullable=True)
    sri_withholding_agent_code:Mapped[str|None]=mapped_column(String(30),nullable=True)
    sri_establishment_code:Mapped[str|None]=mapped_column(String(3),nullable=True)
    sri_emission_point:Mapped[str|None]=mapped_column(String(3),nullable=True)
    sri_invoice_sequence:Mapped[int]=mapped_column(Integer,default=1)
    updated_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=datetime.utcnow,onupdate=datetime.utcnow)
