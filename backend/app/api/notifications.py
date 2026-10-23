import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.api.deps import get_db, require_permission
from app.models import Customer, NotificationLog, NotificationSetting, NotificationTemplate, Sale, SystemSetting, User
from app.schemas.notifications import NotificationSend, NotificationSettingsUpdate, NotificationTemplateUpdate
from app.services.audit import audit
from app.services.notifications import send_email, send_sms, send_whatsapp
from app.services.sri_signing import encrypt_secret

router=APIRouter(prefix="/api/notifications",tags=["Notificaciones"])

def get_cfg(db:Session):
    row=db.scalar(select(NotificationSetting).limit(1))
    if not row:
        row=NotificationSetting()
        db.add(row);db.commit();db.refresh(row)
    return row

def get_system(db:Session):
    row=db.scalar(select(SystemSetting).limit(1))
    if not row: raise HTTPException(400,"Configuración general no encontrada")
    return row

def serialize_cfg(row:NotificationSetting):
    return {
        "id":str(row.id),
        "whatsapp_enabled":row.whatsapp_enabled,
        "whatsapp_phone_number_id":row.whatsapp_phone_number_id,
        "whatsapp_access_token_configured":bool(row.whatsapp_access_token_encrypted),
        "whatsapp_api_version":row.whatsapp_api_version,
        "sms_enabled":row.sms_enabled,
        "sms_provider":row.sms_provider,
        "sms_account_sid":row.sms_account_sid,
        "sms_auth_token_configured":bool(row.sms_auth_token_encrypted),
        "sms_from_number":row.sms_from_number,
        "email_enabled":row.email_enabled,
        "updated_at":row.updated_at,
    }

@router.get("/settings")
def read_settings(db:Session=Depends(get_db),_:User=Depends(require_permission("system.admin"))):
    return serialize_cfg(get_cfg(db))

@router.put("/settings")
def update_settings(payload:NotificationSettingsUpdate,request:Request,db:Session=Depends(get_db),current:User=Depends(require_permission("system.admin"))):
    row=get_cfg(db)
    for k,v in payload.model_dump().items(): setattr(row,k,v)
    audit(db,current,"NOTIFICATION_SETTINGS_UPDATE","notification_settings",row.id,payload.model_dump(),request)
    db.commit();db.refresh(row)
    return serialize_cfg(row)

@router.post("/settings/whatsapp-token")
def save_whatsapp_token(request:Request,token:str,db:Session=Depends(get_db),current:User=Depends(require_permission("system.admin"))):
    if not token.strip(): raise HTTPException(400,"Token requerido")
    row=get_cfg(db);row.whatsapp_access_token_encrypted=encrypt_secret(token.strip())
    audit(db,current,"WHATSAPP_TOKEN_UPDATE","notification_settings",row.id,{},request)
    db.commit()
    return {"ok":True,"configured":True}

@router.post("/settings/sms-token")
def save_sms_token(request:Request,token:str,db:Session=Depends(get_db),current:User=Depends(require_permission("system.admin"))):
    if not token.strip(): raise HTTPException(400,"Token requerido")
    row=get_cfg(db);row.sms_auth_token_encrypted=encrypt_secret(token.strip())
    audit(db,current,"SMS_TOKEN_UPDATE","notification_settings",row.id,{},request)
    db.commit()
    return {"ok":True,"configured":True}

@router.get("/templates")
def templates(db:Session=Depends(get_db),_:User=Depends(require_permission("system.admin"))):
    rows=db.scalars(select(NotificationTemplate).order_by(NotificationTemplate.event_type,NotificationTemplate.channel)).all()
    return [{"id":str(x.id),"event_type":x.event_type,"channel":x.channel,"name":x.name,"subject":x.subject,"body":x.body,"active":x.active} for x in rows]

@router.put("/templates/{template_id}")
def update_template(template_id:uuid.UUID,payload:NotificationTemplateUpdate,request:Request,db:Session=Depends(get_db),current:User=Depends(require_permission("system.admin"))):
    row=db.get(NotificationTemplate,template_id)
    if not row: raise HTTPException(404,"Plantilla no encontrada")
    for k,v in payload.model_dump().items(): setattr(row,k,v)
    audit(db,current,"NOTIFICATION_TEMPLATE_UPDATE","notification_template",row.id,payload.model_dump(),request)
    db.commit();db.refresh(row)
    return {"id":str(row.id)}

@router.get("/logs")
def logs(db:Session=Depends(get_db),_:User=Depends(require_permission("system.admin"))):
    rows=db.scalars(select(NotificationLog).order_by(NotificationLog.created_at.desc()).limit(300)).all()
    return [{"id":str(x.id),"customer_id":str(x.customer_id) if x.customer_id else None,"sale_id":str(x.sale_id) if x.sale_id else None,"event_type":x.event_type,"channel":x.channel,"recipient":x.recipient,"subject":x.subject,"body":x.body,"status":x.status,"provider_message_id":x.provider_message_id,"error":x.error,"created_at":x.created_at,"sent_at":x.sent_at} for x in rows]

@router.post("/send")
def send(payload:NotificationSend,request:Request,db:Session=Depends(get_db),current:User=Depends(require_permission("system.admin"))):
    customer=db.get(Customer,uuid.UUID(payload.customer_id))
    if not customer: raise HTTPException(404,"Cliente no encontrado")
    sale=None
    if payload.sale_id:
        sale=db.get(Sale,uuid.UUID(payload.sale_id))
        if not sale: raise HTTPException(404,"Venta no encontrada")
    cfg=get_cfg(db);system=get_system(db)
    recipient=customer.email if payload.channel=="EMAIL" else (customer.mobile or customer.phone or "")
    log=NotificationLog(customer_id=customer.id,sale_id=sale.id if sale else None,event_type=payload.event_type,channel=payload.channel,recipient=recipient,subject=payload.subject,body=payload.body,status="PENDING",created_by=current.id)
    db.add(log);db.flush()
    try:
        if payload.channel=="WHATSAPP":
            provider_id=send_whatsapp(cfg,customer,payload.body)
        elif payload.channel=="SMS":
            provider_id=send_sms(cfg,customer,payload.body)
        else:
            provider_id=send_email(cfg,system,customer,payload.subject,payload.body)
        log.status="SENT";log.provider_message_id=provider_id;log.sent_at=datetime.now(timezone.utc)
        audit(db,current,"NOTIFICATION_SEND","notification_log",log.id,{"channel":payload.channel,"customer_id":str(customer.id),"event_type":payload.event_type},request)
        db.commit();db.refresh(log)
        return {"ok":True,"id":str(log.id),"status":log.status}
    except Exception as exc:
        log.status="ERROR";log.error=str(exc)
        db.commit()
        raise HTTPException(400,str(exc))
