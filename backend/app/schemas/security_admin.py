from pydantic import BaseModel, EmailStr, Field

class UserCreate(BaseModel):
    identification:str|None=None
    first_name:str=Field(min_length=1,max_length=120)
    last_name:str=Field(min_length=1,max_length=120)
    email:EmailStr
    password:str=Field(min_length=8,max_length=128)
    role_ids:list[str]=[]
    active:bool=True

class UserUpdate(BaseModel):
    identification:str|None=None
    first_name:str=Field(min_length=1,max_length=120)
    last_name:str=Field(min_length=1,max_length=120)
    email:EmailStr
    role_ids:list[str]=[]
    active:bool=True

class PasswordReset(BaseModel):
    password:str=Field(min_length=8,max_length=128)

class RoleUpdate(BaseModel):
    description:str|None=None
    permission_ids:list[str]=[]
    active:bool=True
