from pathlib import Path
from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.api.deps import get_db, require_permission
from app.config import settings
from app.models import SystemSetting, User
from app.schemas.settings import BackupSettingsUpdate, SystemSettingsUpdate
from app.services.audit import audit
from app.services.backup import RCLONE_CONFIG, rclone_config_present, test_remote

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
        "backup_enabled":row.backup_enabled,
        "backup_provider":row.backup_provider,
        "backup_remote_name":row.backup_remote_name,
        "backup_folder":row.backup_folder,
        "backup_time":row.backup_time,
        "backup_keep_last":2,
        "backup_configured":rclone_config_present(),
        "backup_last_run":row.backup_last_run,
        "backup_last_status":row.backup_last_status,
        "backup_last_filename":row.backup_last_filename,
        "backup_last_error":row.backup_last_error,
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


@router.put("/backup")
def update_backup_settings(payload:BackupSettingsUpdate,request:Request,db:Session=Depends(get_db),current:User=Depends(require_permission("system.admin"))):
    row=get_settings(db)
    old={
        "backup_enabled":row.backup_enabled,
        "backup_provider":row.backup_provider,
        "backup_remote_name":row.backup_remote_name,
        "backup_folder":row.backup_folder,
        "backup_time":row.backup_time,
    }
    row.backup_enabled=payload.backup_enabled
    row.backup_provider=payload.backup_provider
    row.backup_remote_name=payload.backup_remote_name.strip()
    row.backup_folder=payload.backup_folder.strip().strip("/")
    row.backup_time=payload.backup_time
    row.backup_keep_last=2
    audit(db,current,"BACKUP_SETTINGS_UPDATE","system_settings",row.id,{"old":old,"new":{
        "backup_enabled":row.backup_enabled,
        "backup_provider":row.backup_provider,
        "backup_remote_name":row.backup_remote_name,
        "backup_folder":row.backup_folder,
        "backup_time":row.backup_time,
        "backup_keep_last":2,
    }},request)
    db.commit();db.refresh(row)
    return serialize(row)

@router.post("/backup/rclone-config")
async def upload_rclone_config(request:Request,file:UploadFile=File(...),db:Session=Depends(get_db),current:User=Depends(require_permission("system.admin"))):
    data=await file.read()
    if not data or len(data)>512*1024:
        raise HTTPException(400,"Archivo rclone.conf vacío o demasiado grande")
    try:
        text=data.decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(400,"El archivo rclone.conf debe ser texto UTF-8")
    if "[" not in text or "]" not in text or "type =" not in text:
        raise HTTPException(400,"El archivo no parece ser una configuración válida de rclone")
    RCLONE_CONFIG.parent.mkdir(parents=True,exist_ok=True)
    RCLONE_CONFIG.write_bytes(data)
    RCLONE_CONFIG.chmod(0o600)
    row=get_settings(db)
    audit(db,current,"BACKUP_RCLONE_CONFIG_UPLOAD","system_settings",row.id,{"filename":file.filename},request)
    db.commit()
    return {"ok":True,"configured":True}

@router.post("/backup/test")
def test_backup_connection(request:Request,db:Session=Depends(get_db),current:User=Depends(require_permission("system.admin"))):
    row=get_settings(db)
    try:
        test_remote(row.backup_remote_name)
    except Exception as exc:
        raise HTTPException(400,str(exc))
    audit(db,current,"BACKUP_CONNECTION_TEST","system_settings",row.id,{"remote":row.backup_remote_name,"provider":row.backup_provider},request)
    db.commit()
    return {"ok":True,"message":"Conexión con la nube verificada correctamente"}

@router.post("/backup/run")
def request_backup(request:Request,db:Session=Depends(get_db),current:User=Depends(require_permission("system.admin"))):
    row=get_settings(db)
    if not rclone_config_present():
        raise HTTPException(400,"Primero debe cargar rclone.conf")
    if not row.backup_remote_name.strip():
        raise HTTPException(400,"Debe configurar el nombre del remoto")
    if row.backup_last_status=="RUNNING":
        raise HTTPException(409,"Ya hay un respaldo en ejecución")
    row.backup_run_requested=True
    row.backup_last_status="QUEUED"
    row.backup_last_error=None
    audit(db,current,"BACKUP_RUN_REQUESTED","system_settings",row.id,{"provider":row.backup_provider,"remote":row.backup_remote_name},request)
    db.commit()
    return {"ok":True,"message":"Respaldo agregado a la cola"}
