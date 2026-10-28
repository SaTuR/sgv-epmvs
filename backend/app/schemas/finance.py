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
    confirmation_date:date|None=None
    sale_price:Decimal=Field(gt=0)
    down_payment:Decimal=Field(default=0,ge=0)
    installment_count:int=Field(default=1,ge=1,le=360)
    frequency:str="MONTHLY"
    first_due_date:date
    notes:str|None=None

class PaymentCreate(BaseModel):
    sale_id:str
    payment_date:date|None=None
    amount:Decimal=Field(gt=0)
    payment_method:str
    reference:str|None=None
    notes:str|None=None


class InstallmentUpdateItem(BaseModel):
    id: str
    due_date: date
    amount: Decimal = Field(gt=0)

class InstallmentsUpdate(BaseModel):
    installments: list[InstallmentUpdateItem] = Field(min_length=1)


class DownPaymentUpdate(BaseModel):
    down_payment: Decimal = Field(ge=0)
    mode: str = Field(default="AUTO", pattern="^(AUTO|MANUAL)$")
    installments: list[InstallmentUpdateItem] | None = None
