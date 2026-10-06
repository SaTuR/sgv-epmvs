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
    backup_time:str=Field(pattern="^(?:[01]\d|2[0-3]):[0-5]\d$")
    backup_keep_last:int=Field(default=2,ge=2,le=30)
