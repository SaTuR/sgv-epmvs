from datetime import date
from decimal import Decimal
from pydantic import BaseModel, Field

class ReservationCreate(BaseModel):
    customer_id:str
    property_id:str
    reservation_date:date|None=None
    expires_on:date|None=None
    notes:str|None=None

class SaleCreate(BaseModel):
    customer_id:str
    property_id:str
    reservation_id:str|None=None
    seller_id:str
    confirmation_date:date|None=None
    sale_price:Decimal=Field(gt=0)
    down_payment:Decimal=Field(default=0,ge=0)
    down_payment_date:date|None=None
    down_payment_method:str|None=None
    down_payment_reference:str|None=None
    down_payment_bank_receipt:str|None=None
    installment_count:int=Field(default=1,ge=1,le=360)
    frequency:str="MONTHLY"
    first_due_date:date
    notes:str|None=None

class PaymentCreate(BaseModel):
    sale_id:str
    payment_date:date|None=None
    amount:Decimal=Field(gt=0)
    payment_method:str
    reference:str=Field(min_length=1,max_length=120)
    bank_receipt:str=Field(min_length=1,max_length=120)
    notes:str|None=None

class PaymentUpdate(BaseModel):
    payment_date:date
    payment_method:str=Field(min_length=1,max_length=30)
    reference:str=Field(min_length=1,max_length=120)
    bank_receipt:str=Field(min_length=1,max_length=120)
    notes:str|None=None


class InstallmentUpdateItem(BaseModel):
    id: str
    due_date: date
    amount: Decimal = Field(gt=0)

class InstallmentsUpdate(BaseModel):
    installments: list[InstallmentUpdateItem] = Field(min_length=1)


class DownPaymentUpdate(BaseModel):
    down_payment: Decimal = Field(ge=0)
    down_payment_date: date | None = None
    down_payment_method: str | None = None
    down_payment_reference: str | None = None
    down_payment_bank_receipt: str | None = None
    mode: str = Field(default="AUTO", pattern="^(AUTO|MANUAL)$")
    installments: list[InstallmentUpdateItem] | None = None


class SellerAssignment(BaseModel):
    seller_id: str
