import uuid
from datetime import date, datetime
from decimal import Decimal
from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Numeric, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db import Base

class Customer(Base):
    __tablename__ = "customers"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    identification_type: Mapped[str] = mapped_column(String(20), default="CEDULA")
    identification: Mapped[str] = mapped_column(String(30), unique=True, index=True)
    first_name: Mapped[str] = mapped_column(String(120))
    last_name: Mapped[str] = mapped_column(String(120))
    birth_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    marital_status: Mapped[str | None] = mapped_column(String(40), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    mobile: Mapped[str | None] = mapped_column(String(30), nullable=True)
    email: Mapped[str | None] = mapped_column(String(180), nullable=True)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    canton: Mapped[str | None] = mapped_column(String(100), nullable=True)
    province: Mapped[str | None] = mapped_column(String(100), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()

class StageMap(Base):
    __tablename__ = "stage_maps"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    stage_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("project_stages.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(160))
    file_path: Mapped[str] = mapped_column(String(500))
    file_type: Mapped[str] = mapped_column(String(50))
    version: Mapped[int] = mapped_column(default=1)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

class Block(Base):
    __tablename__ = "blocks"
    __table_args__ = (UniqueConstraint("stage_id", "name", name="uq_block_stage_name"),)
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    stage_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("project_stages.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(80))
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)

class PropertyStatus(Base):
    __tablename__ = "property_statuses"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(80), unique=True)
    sort_order: Mapped[int] = mapped_column(default=0)
    active: Mapped[bool] = mapped_column(Boolean, default=True)

class Property(Base):
    __tablename__ = "properties"
    __table_args__ = (UniqueConstraint("block_id", "lot_number", name="uq_property_block_lot"),)
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    block_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("blocks.id", ondelete="RESTRICT"), index=True)
    status_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("property_statuses.id", ondelete="RESTRICT"), index=True)
    code: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    lot_number: Mapped[str] = mapped_column(String(40))
    cadastral_key: Mapped[str | None] = mapped_column(String(100), nullable=True)
    area_m2: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    price_per_m2: Mapped[Decimal | None] = mapped_column(Numeric(14, 4), nullable=True)
    total_price: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    location_reference: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    status: Mapped[PropertyStatus] = relationship(lazy="joined")
    block: Mapped[Block] = relationship(lazy="joined")
