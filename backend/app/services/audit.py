import json
from fastapi import Request
from sqlalchemy.orm import Session
from app.models.audit import AuditLog

def audit(db:Session,user,action:str,target_type:str,target_id=None,details=None,request:Request|None=None):
    ip=None
    if request:
        forwarded=request.headers.get("x-forwarded-for")
        ip=(forwarded.split(",")[0].strip() if forwarded else (request.client.host if request.client else None))
    item=AuditLog(
        user_id=getattr(user,"id",None),
        user_email=getattr(user,"email",None),
        action=action,
        target_type=target_type,
        target_id=str(target_id) if target_id is not None else None,
        ip_address=ip,
        details=json.dumps(details,ensure_ascii=False,default=str) if details is not None else None,
    )
    db.add(item)
    db.flush()
