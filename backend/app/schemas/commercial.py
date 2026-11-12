from decimal import Decimal
from pydantic import BaseModel, EmailStr, Field

class SellerCreate(BaseModel):
    identification:str=Field(min_length=3,max_length=20)
    first_name:str=Field(min_length=1,max_length=100)
    last_name:str=Field(min_length=1,max_length=100)
    phone:str|None=None
    email:EmailStr|None=None
    seller_type:str=Field(default="INTERNAL",pattern="^(INTERNAL|EXTERNAL)$")
    default_commission_rate:Decimal=Field(default=0,ge=0,le=100)

class SellerUpdate(SellerCreate):
    active:bool=True

class CommissionStatusUpdate(BaseModel):
    status:str=Field(pattern="^(PENDING|APPROVED|PAID|CANCELLED)$")
    payment_reference:str|None=None
    notes:str|None=None
