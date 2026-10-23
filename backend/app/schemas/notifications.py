from pydantic import BaseModel, Field

class NotificationSettingsUpdate(BaseModel):
    whatsapp_enabled:bool=False
    whatsapp_phone_number_id:str|None=None
    whatsapp_api_version:str=Field(default="v24.0",max_length=20)
    sms_enabled:bool=False
    sms_provider:str=Field(default="TWILIO",pattern="^TWILIO$")
    sms_account_sid:str|None=None
    sms_from_number:str|None=None
    email_enabled:bool=False

class NotificationTemplateUpdate(BaseModel):
    name:str=Field(min_length=1,max_length=120)
    subject:str|None=Field(default=None,max_length=300)
    body:str=Field(min_length=1,max_length=5000)
    active:bool=True

class NotificationSend(BaseModel):
    customer_id:str
    sale_id:str|None=None
    channel:str=Field(pattern="^(WHATSAPP|SMS|EMAIL)$")
    event_type:str=Field(default="MANUAL",max_length=50)
    subject:str|None=Field(default=None,max_length=300)
    body:str=Field(min_length=1,max_length=5000)
