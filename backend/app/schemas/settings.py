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


class BackupSettingsUpdate(BaseModel):
    backup_enabled:bool=False
    backup_provider:str=Field(pattern="^(GDRIVE|ONEDRIVE|DROPBOX)$")
    backup_remote_name:str=Field(min_length=1,max_length=120)
    backup_folder:str=Field(min_length=1,max_length=255)
    backup_time:str=Field(pattern=r"^(?:[01]\d|2[0-3]):[0-5]\d$")
    backup_keep_last:int=Field(default=2,ge=2,le=30)


class SriSettingsUpdate(BaseModel):
    sri_enabled:bool=False
    sri_environment:str=Field(pattern="^(TEST|PRODUCTION)$")
    sri_ruc:str=Field(min_length=13,max_length=13)
    sri_business_name:str=Field(min_length=1,max_length=300)
    sri_trade_name:str|None=None
    sri_accounting_required:bool=True
    sri_special_taxpayer_code:str|None=None
    sri_withholding_agent_code:str|None=None
    sri_establishment_code:str=Field(pattern=r"^\d{3}$")
    sri_emission_point:str=Field(pattern=r"^\d{3}$")
    sri_invoice_sequence:int=Field(ge=1,le=999999999)
    sri_tax_code:str=Field(min_length=1,max_length=2)
    sri_tax_percentage_code:str=Field(min_length=1,max_length=4)
    sri_tax_rate:float=Field(ge=0,le=100)
    sri_prices_include_tax:bool=True
    sri_payment_method_code:str=Field(min_length=2,max_length=2)
    sri_software_provider_ruc:str|None=None


class RideSettingsUpdate(BaseModel):
    ride_title:str=Field(min_length=1,max_length=180)
    ride_subtitle:str|None=None
    ride_footer:str=Field(min_length=1,max_length=500)
    ride_additional_text:str|None=None
    ride_page_size:str=Field(pattern=r"^(A4|LETTER)$")
    ride_show_logo:bool=True
    ride_show_qr:bool=True
    ride_qr_size_mm:int=Field(ge=15,le=50)
    ride_qr_content_template:str=Field(min_length=1,max_length=800)
    ride_primary_hex:str=Field(pattern=r"^#[0-9A-Fa-f]{6}$")


class InvoiceEmailSettingsUpdate(BaseModel):
    invoice_email_enabled:bool=False
    invoice_email_send_on_authorization:bool=False
    smtp_host:str|None=None
    smtp_port:int=Field(ge=1,le=65535)
    smtp_security:str=Field(pattern=r"^(NONE|STARTTLS|SSL)$")
    smtp_username:str|None=None
    smtp_sender_email:EmailStr|None=None
    smtp_sender_name:str|None=None
    invoice_email_subject_template:str=Field(min_length=1,max_length=500)
    invoice_email_body_template:str=Field(min_length=1,max_length=5000)
    invoice_email_attach_ride:bool=True
    invoice_email_attach_xml:bool=True
    invoice_email_cc:str|None=None
    invoice_email_bcc:str|None=None
    invoice_email_retries:int=Field(ge=0,le=10)
    invoice_email_timeout_seconds:int=Field(ge=5,le=120)
