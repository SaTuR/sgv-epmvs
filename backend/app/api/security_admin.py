import json
import uuid
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.api.deps import get_db, require_permission
from app.core.security import hash_password
from app.models import AuditLog, Permission, Role, User
from app.schemas.security_admin import PasswordReset, RoleUpdate, UserCreate, UserUpdate
from app.services.audit import audit

router=APIRouter(prefix="/api/security",tags=["Usuarios, roles y auditoría"])

def role_dict(r:Role):
    return {"id":str(r.id),"name":r.name,"description":r.description,"active":r.active,
      "permissions":[{"id":str(p.id),"code":p.code,"name":p.name} for p in sorted(r.permissions,key=lambda x:x.code)]}

def user_dict(u:User):
    return {"id":str(u.id),"identification":u.identification,"first_name":u.first_name,"last_name":u.last_name,
      "full_name":u.full_name,"email":u.email,"active":u.active,
      "roles":[{"id":str(r.id),"name":r.name} for r in sorted(u.roles,key=lambda x:x.name)],
      "created_at":u.created_at}

@router.get("/users")
def users(db:Session=Depends(get_db),_:User=Depends(require_permission("users.manage"))):
    return [user_dict(u) for u in db.scalars(select(User).order_by(User.last_name,User.first_name)).all()]

@router.post("/users")
def create_user(payload:UserCreate,request:Request,db:Session=Depends(get_db),current:User=Depends(require_permission("users.manage"))):
    roles=db.scalars(select(Role).where(Role.id.in_([uuid.UUID(x) for x in payload.role_ids]))).all() if payload.role_ids else []
    u=User(identification=payload.identification,first_name=payload.first_name,last_name=payload.last_name,
      email=payload.email.lower().strip(),password_hash=hash_password(payload.password),active=payload.active,roles=roles)
    db.add(u)
    try:
        db.flush()
        audit(db,current,"USER_CREATE","user",u.id,{"email":u.email,"roles":[r.name for r in roles]},request)
        db.commit()
    except IntegrityError:
        db.rollback();raise HTTPException(409,"La identificación o el correo ya están registrados")
    db.refresh(u);return user_dict(u)

@router.put("/users/{user_id}")
def update_user(user_id:uuid.UUID,payload:UserUpdate,request:Request,db:Session=Depends(get_db),current:User=Depends(require_permission("users.manage"))):
    u=db.get(User,user_id)
    if not u: raise HTTPException(404,"Usuario no encontrado")
    old={"identification":u.identification,"first_name":u.first_name,"last_name":u.last_name,"email":u.email,"active":u.active,"roles":[r.name for r in u.roles]}
    roles=db.scalars(select(Role).where(Role.id.in_([uuid.UUID(x) for x in payload.role_ids]))).all() if payload.role_ids else []
    u.identification=payload.identification;u.first_name=payload.first_name;u.last_name=payload.last_name
    u.email=payload.email.lower().strip();u.active=payload.active;u.roles=roles
    try:
        audit(db,current,"USER_UPDATE","user",u.id,{"old":old,"new":{"identification":u.identification,"first_name":u.first_name,"last_name":u.last_name,"email":u.email,"active":u.active,"roles":[r.name for r in roles]}},request)
        db.commit()
    except IntegrityError:
        db.rollback();raise HTTPException(409,"La identificación o el correo ya están registrados")
    db.refresh(u);return user_dict(u)

@router.post("/users/{user_id}/password")
def reset_password(user_id:uuid.UUID,payload:PasswordReset,request:Request,db:Session=Depends(get_db),current:User=Depends(require_permission("users.manage"))):
    u=db.get(User,user_id)
    if not u: raise HTTPException(404,"Usuario no encontrado")
    u.password_hash=hash_password(payload.password)
    audit(db,current,"USER_PASSWORD_RESET","user",u.id,{"email":u.email},request)
    db.commit();return {"ok":True}

@router.get("/roles")
def roles(db:Session=Depends(get_db),_:User=Depends(require_permission("roles.manage"))):
    return [role_dict(r) for r in db.scalars(select(Role).order_by(Role.name)).all()]

@router.get("/permissions")
def permissions(db:Session=Depends(get_db),_:User=Depends(require_permission("roles.manage"))):
    rows=db.scalars(select(Permission).order_by(Permission.code)).all()
    return [{"id":str(p.id),"code":p.code,"name":p.name} for p in rows]

@router.put("/roles/{role_id}")
def update_role(role_id:uuid.UUID,payload:RoleUpdate,request:Request,db:Session=Depends(get_db),current:User=Depends(require_permission("roles.manage"))):
    role=db.get(Role,role_id)
    if not role: raise HTTPException(404,"Rol no encontrado")
    old={"description":role.description,"active":role.active,"permissions":[p.code for p in role.permissions]}
    perms=db.scalars(select(Permission).where(Permission.id.in_([uuid.UUID(x) for x in payload.permission_ids]))).all() if payload.permission_ids else []
    if role.name=="Administrador":
        all_perms=db.scalars(select(Permission)).all()
        perms=all_perms
        role.active=True
    else:
        role.active=payload.active
    role.description=payload.description
    role.permissions=perms
    audit(db,current,"ROLE_UPDATE","role",role.id,{"old":old,"new":{"description":role.description,"active":role.active,"permissions":[p.code for p in perms]}},request)
    db.commit();db.refresh(role);return role_dict(role)

@router.get("/audit")
def audit_logs(
    action:str|None=None,target_type:str|None=None,user_email:str|None=None,limit:int=200,
    db:Session=Depends(get_db),_:User=Depends(require_permission("audit.view"))
):
    stmt=select(AuditLog).order_by(AuditLog.created_at.desc()).limit(min(max(limit,1),500))
    if action: stmt=stmt.where(AuditLog.action==action)
    if target_type: stmt=stmt.where(AuditLog.target_type==target_type)
    if user_email: stmt=stmt.where(AuditLog.user_email.ilike("%"+user_email.strip()+"%"))
    rows=db.scalars(stmt).all()
    out=[]
    for x in rows:
        try: details=json.loads(x.details) if x.details else None
        except Exception: details=x.details
        out.append({"id":str(x.id),"user_email":x.user_email,"action":x.action,"target_type":x.target_type,
          "target_id":x.target_id,"ip_address":x.ip_address,"details":details,"created_at":x.created_at})
    return out
