from pathlib import Path
from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.api.deps import get_db, require_permission
from app.config import settings
from app.models import SystemSetting, User
from app.schemas.settings import BackupSettingsUpdate, InvoiceEmailSettingsUpdate, RideSettingsUpdate, SriSettingsUpdate, SystemSettingsUpdate
from app.services.audit import audit
from app.services.backup import RCLONE_CONFIG, rclone_config_present, test_remote
from app.services.sri_signing import certificate_ready, encrypt_secret, install_certificate

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
        "sri_enabled":row.sri_enabled,
        "sri_environment":row.sri_environment,
        "sri_ruc":row.sri_ruc,
        "sri_business_name":row.sri_business_name,
        "sri_trade_name":row.sri_trade_name,
        "sri_accounting_required":row.sri_accounting_required,
        "sri_special_taxpayer_code":row.sri_special_taxpayer_code,
        "sri_withholding_agent_code":row.sri_withholding_agent_code,
        "sri_establishment_code":row.sri_establishment_code,
        "sri_emission_point":row.sri_emission_point,
        "sri_invoice_sequence":row.sri_invoice_sequence,
        "sri_tax_code":row.sri_tax_code,
        "sri_tax_percentage_code":row.sri_tax_percentage_code,
        "sri_tax_rate":float(row.sri_tax_rate or 0),
        "sri_prices_include_tax":row.sri_prices_include_tax,
        "sri_payment_method_code":row.sri_payment_method_code,
        "sri_software_provider_ruc":row.sri_software_provider_ruc,
        "sri_certificate_configured":certificate_ready(row),
        "sri_certificate_subject":row.sri_certificate_subject,
        "sri_certificate_issuer":row.sri_certificate_issuer,
        "sri_certificate_serial":row.sri_certificate_serial,
        "sri_certificate_valid_from":row.sri_certificate_valid_from,
        "sri_certificate_valid_to":row.sri_certificate_valid_to,
        "ride_title":row.ride_title,
        "ride_subtitle":row.ride_subtitle,
        "ride_footer":row.ride_footer,
        "ride_additional_text":row.ride_additional_text,
        "ride_page_size":row.ride_page_size,
        "ride_show_logo":row.ride_show_logo,
        "ride_logo_configured":bool(row.ride_logo_path and Path(row.ride_logo_path).is_file()),
        "ride_show_qr":row.ride_show_qr,
        "ride_qr_size_mm":row.ride_qr_size_mm,
        "ride_qr_content_template":row.ride_qr_content_template,
        "ride_primary_hex":row.ride_primary_hex,
        "ride_code_type":row.ride_code_type,
        "ride_barcode_height_mm":row.ride_barcode_height_mm,
        "ride_show_payment_table":row.ride_show_payment_table,
        "ride_show_additional_info":row.ride_show_additional_info,
        "invoice_email_enabled":row.invoice_email_enabled,
        "invoice_email_send_on_authorization":row.invoice_email_send_on_authorization,
        "smtp_host":row.smtp_host,
        "smtp_port":row.smtp_port,
        "smtp_security":row.smtp_security,
        "smtp_username":row.smtp_username,
        "smtp_password_configured":bool(row.smtp_password_encrypted),
        "smtp_sender_email":row.smtp_sender_email,
        "smtp_sender_name":row.smtp_sender_name,
        "invoice_email_subject_template":row.invoice_email_subject_template,
        "invoice_email_body_template":row.invoice_email_body_template,
        "invoice_email_attach_ride":row.invoice_email_attach_ride,
        "invoice_email_attach_xml":row.invoice_email_attach_xml,
        "invoice_email_cc":row.invoice_email_cc,
        "invoice_email_bcc":row.invoice_email_bcc,
        "invoice_email_retries":row.invoice_email_retries,
        "invoice_email_timeout_seconds":row.invoice_email_timeout_seconds,
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


@router.put("/sri")
def update_sri_settings(payload:SriSettingsUpdate,request:Request,db:Session=Depends(get_db),current:User=Depends(require_permission("system.admin"))):
    row=get_settings(db)
    old={
        "sri_enabled":row.sri_enabled,
        "sri_environment":row.sri_environment,
        "sri_ruc":row.sri_ruc,
        "sri_business_name":row.sri_business_name,
        "sri_trade_name":row.sri_trade_name,
        "sri_accounting_required":row.sri_accounting_required,
        "sri_special_taxpayer_code":row.sri_special_taxpayer_code,
        "sri_withholding_agent_code":row.sri_withholding_agent_code,
        "sri_establishment_code":row.sri_establishment_code,
        "sri_emission_point":row.sri_emission_point,
        "sri_invoice_sequence":row.sri_invoice_sequence,
        "sri_tax_code":row.sri_tax_code,
        "sri_tax_percentage_code":row.sri_tax_percentage_code,
        "sri_tax_rate":float(row.sri_tax_rate or 0),
        "sri_payment_method_code":row.sri_payment_method_code,
        "sri_software_provider_ruc":row.sri_software_provider_ruc,
    }
    for k,v in payload.model_dump().items():
        setattr(row,k,v)
    audit(db,current,"SRI_SETTINGS_UPDATE","system_settings",row.id,{"old":old,"new":payload.model_dump()},request)
    db.commit();db.refresh(row)
    return serialize(row)


@router.post("/sri/certificate")
async def upload_sri_certificate(
    request:Request,
    password:str=Form(...),
    file:UploadFile=File(...),
    db:Session=Depends(get_db),
    current:User=Depends(require_permission("system.admin")),
):
    filename=(file.filename or "").lower()
    if not (filename.endswith(".p12") or filename.endswith(".pfx")):
        raise HTTPException(400,"El certificado debe ser un archivo .p12 o .pfx")
    data=await file.read()
    if not data or len(data)>5*1024*1024:
        raise HTTPException(400,"El certificado está vacío o supera 5 MB")
    if not password:
        raise HTTPException(400,"Debe ingresar la contraseña del certificado")
    row=get_settings(db)
    try:
        info=install_certificate(data,password,row)
    except ValueError as exc:
        raise HTTPException(400,str(exc))
    audit(db,current,"SRI_CERTIFICATE_UPLOAD","system_settings",row.id,{
        "filename":file.filename,
        "subject":info["subject"],
        "issuer":info["issuer"],
        "serial":info["serial"],
        "valid_from":str(info["valid_from"]),
        "valid_to":str(info["valid_to"]),
    },request)
    db.commit();db.refresh(row)
    return serialize(row)


@router.put("/ride")
def update_ride_settings(payload:RideSettingsUpdate,request:Request,db:Session=Depends(get_db),current:User=Depends(require_permission("system.admin"))):
    row=get_settings(db)
    old={k:getattr(row,k) for k in payload.model_fields.keys()}
    for k,v in payload.model_dump().items():
        setattr(row,k,v)
    audit(db,current,"RIDE_SETTINGS_UPDATE","system_settings",row.id,{"old":old,"new":payload.model_dump()},request)
    db.commit();db.refresh(row)
    return serialize(row)


@router.post("/ride/logo")
async def upload_ride_logo(request:Request,file:UploadFile=File(...),db:Session=Depends(get_db),current:User=Depends(require_permission("system.admin"))):
    filename=(file.filename or "").lower()
    if not filename.endswith((".png",".jpg",".jpeg",".webp")):
        raise HTTPException(400,"El logo debe ser PNG, JPG, JPEG o WEBP")
    data=await file.read()
    if not data or len(data)>5*1024*1024:
        raise HTTPException(400,"El logo está vacío o supera 5 MB")
    suffix=Path(filename).suffix or ".png"
    logo_dir=Path(settings.upload_path)/"branding"
    logo_dir.mkdir(parents=True,exist_ok=True)
    path=logo_dir/f"ride-logo{suffix}"
    path.write_bytes(data);path.chmod(0o600)
    row=get_settings(db);row.ride_logo_path=str(path)
    audit(db,current,"RIDE_LOGO_UPLOAD","system_settings",row.id,{"filename":file.filename},request)
    db.commit();db.refresh(row)
    return serialize(row)


@router.put("/invoice-email")
def update_invoice_email_settings(payload:InvoiceEmailSettingsUpdate,request:Request,db:Session=Depends(get_db),current:User=Depends(require_permission("system.admin"))):
    row=get_settings(db)
    old={k:getattr(row,k) for k in payload.model_fields.keys()}
    for k,v in payload.model_dump().items():
        setattr(row,k,v)
    audit(db,current,"INVOICE_EMAIL_SETTINGS_UPDATE","system_settings",row.id,{"old":old,"new":payload.model_dump()},request)
    db.commit();db.refresh(row)
    return serialize(row)


@router.post("/invoice-email/password")
def update_invoice_email_password(request:Request,password:str=Form(...),db:Session=Depends(get_db),current:User=Depends(require_permission("system.admin"))):
    if not password:
        raise HTTPException(400,"Debe ingresar la contraseña SMTP")
    row=get_settings(db)
    row.smtp_password_encrypted=encrypt_secret(password)
    audit(db,current,"SMTP_PASSWORD_UPDATE","system_settings",row.id,{},request)
    db.commit();db.refresh(row)
    return serialize(row)
