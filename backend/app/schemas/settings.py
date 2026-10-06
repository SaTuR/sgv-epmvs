from pydantic import BaseModel, EmailStr, Field

class SystemSettingsUpdate(BaseModel):
    institution_name:str=Field(min_length=1,max_length=200)
    tax_id:str|None=None
    address:str|None=None
    phone:str|None=None
    email:EmailStr|None=None
    city:str=Field(min_length=1,max_length=100)
    province:str=Field(min_length=1,max_length=100)
    reservation_default_days:int=Field(ge=1,le=365)
    currency_symbol:str=Field(min_length=1,max_length=10)
    public_base_url:str=Field(min_length=1,max_length=500)
    document_footer:str=Field(min_length=1,max_length=255)
    timezone:str=Field(min_length=1,max_length=80)
