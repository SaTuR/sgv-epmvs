from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.api.deps import get_db, require_permission
from app.config import settings
from app.models import SystemSetting, User
from app.schemas.settings import SystemSettingsUpdate
from app.services.audit import audit

router=APIRouter(prefix="/api/settings",tags=["Configuración"])

def get_settings(db:Session):
    row=db.scalar(select(SystemSetting).limit(1))
    if not row:
        row=SystemSetting(public_base_url=settings.public_base_url,timezone=settings.tz)
        db.add(row);db.commit();db.refresh(row)
    return row

def serialize(row:SystemSetting):
    return {
        "id":str(row.id),
        "institution_name":row.institution_name,
        "tax_id":row.tax_id,
        "address":row.address,
        "phone":row.phone,
        "email":row.email,
        "city":row.city,
        "province":row.province,
        "reservation_default_days":row.reservation_default_days,
        "currency_symbol":row.currency_symbol,
        "public_base_url":row.public_base_url,
        "document_footer":row.document_footer,
        "timezone":row.timezone,
        "updated_at":row.updated_at,
    }

@router.get("")
def read_settings(db:Session=Depends(get_db),_:User=Depends(require_permission("system.admin"))):
    return serialize(get_settings(db))

@router.put("")
def update_settings(payload:SystemSettingsUpdate,request:Request,db:Session=Depends(get_db),current:User=Depends(require_permission("system.admin"))):
    row=get_settings(db)
    old=serialize(row)
    for k,v in payload.model_dump().items():
        setattr(row,k,v)
    audit(db,current,"SYSTEM_SETTINGS_UPDATE","system_settings",row.id,{"old":old,"new":payload.model_dump()},request)
    db.commit();db.refresh(row)
    return serialize(row)

@router.get("/runtime")
def runtime_settings(db:Session=Depends(get_db),_:User=Depends(require_permission("sales.manage"))):
    row=get_settings(db)
    return {
        "reservation_default_days":row.reservation_default_days,
        "currency_symbol":row.currency_symbol,
    }
