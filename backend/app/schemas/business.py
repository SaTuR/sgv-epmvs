from datetime import date
from decimal import Decimal
from pydantic import BaseModel, EmailStr, Field

class CustomerCreate(BaseModel):
    identification_type: str = "CEDULA"
    identification: str = Field(min_length=3, max_length=30)
    first_name: str = Field(min_length=1, max_length=120)
    last_name: str = Field(min_length=1, max_length=120)
    birth_date: date | None = None
    marital_status: str | None = None
    phone: str | None = None
    mobile: str | None = None
    email: EmailStr | None = None
    address: str | None = None
    canton: str | None = None
    province: str | None = None
    notes: str | None = None

class CustomerUpdate(CustomerCreate):
    active: bool = True

class BlockCreate(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    description: str | None = None

class PropertyCreate(BaseModel):
    block_id: str
    status_code: str = "AVAILABLE"
    code: str = Field(min_length=1, max_length=80)
    lot_number: str = Field(min_length=1, max_length=40)
    cadastral_key: str | None = None
    area_m2: Decimal = Field(gt=0)
    price_per_m2: Decimal | None = Field(default=None, ge=0)
    total_price: Decimal = Field(ge=0)
    location_reference: str | None = None
    notes: str | None = None
