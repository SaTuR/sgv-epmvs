import uuid
from decimal import Decimal
from pathlib import Path
from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.api.deps import get_current_user, get_db, require_permission
from app.config import settings
from app.models import Block, Customer, Project, ProjectStage, Property, PropertyStatus, Reservation, Sale, StageMap, User
from app.schemas.business import BlockCreate, CustomerCreate, CustomerUpdate, PropertyCreate, PropertyUpdate
from app.services.audit import audit

router = APIRouter(prefix="/api", tags=["Gestión comercial"])

def customer_dict(c: Customer):
    return {"id":str(c.id),"identification_type":c.identification_type,"identification":c.identification,
        "first_name":c.first_name,"last_name":c.last_name,"full_name":c.full_name,"birth_date":c.birth_date,
        "marital_status":c.marital_status,"phone":c.phone,"mobile":c.mobile,"email":c.email,
        "address":c.address,"canton":c.canton,"province":c.province,"notes":c.notes,"active":c.active}

@router.get("/customers")
def list_customers(q: str | None = None, db: Session = Depends(get_db), _: User = Depends(require_permission("customers.manage"))):
    stmt = select(Customer).order_by(Customer.last_name, Customer.first_name)
    if q:
        term=f"%{q.strip()}%"
        stmt=stmt.where((Customer.identification.ilike(term)) | (Customer.first_name.ilike(term)) | (Customer.last_name.ilike(term)))
    return [customer_dict(x) for x in db.scalars(stmt).all()]

@router.post("/customers")
def create_customer(payload: CustomerCreate, request: Request, db: Session = Depends(get_db), current: User = Depends(require_permission("customers.manage"))):
    c=Customer(**payload.model_dump())
    db.add(c)
    try:
        db.flush()
        audit(db,current,"CUSTOMER_CREATE","customer",c.id,{"identification":c.identification,"name":c.full_name},request)
        db.commit()
    except IntegrityError:
        db.rollback(); raise HTTPException(409, "Ya existe un cliente con esa identificación")
    db.refresh(c); return customer_dict(c)

@router.put("/customers/{customer_id}")
def update_customer(customer_id: uuid.UUID, payload: CustomerUpdate, request: Request, db: Session = Depends(get_db), current: User = Depends(require_permission("customers.manage"))):
    c=db.get(Customer,customer_id)
    if not c: raise HTTPException(404,"Cliente no encontrado")
    old=customer_dict(c)
    for k,v in payload.model_dump().items(): setattr(c,k,v)
    try:
        audit(db,current,"CUSTOMER_UPDATE","customer",c.id,{"old":old,"new":customer_dict(c)},request)
        db.commit()
    except IntegrityError:
        db.rollback(); raise HTTPException(409,"La identificación ya pertenece a otro cliente")
    db.refresh(c); return customer_dict(c)

@router.get("/projects")
def projects(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    rows=db.scalars(select(Project).where(Project.active.is_(True)).order_by(Project.name)).all()
    return [{"id":str(p.id),"name":p.name,"description":p.description,
      "stages":[{"id":str(s.id),"name":s.name,"description":s.description,"active":s.active} for s in p.stages]} for p in rows]

@router.get("/stages/{stage_id}/maps")
def maps(stage_id: uuid.UUID, db: Session=Depends(get_db), _:User=Depends(get_current_user)):
    rows=db.scalars(select(StageMap).where(StageMap.stage_id==stage_id).order_by(StageMap.version.desc())).all()
    return [{"id":str(x.id),"name":x.name,"file_path":x.file_path,"file_type":x.file_type,"version":x.version,"is_active":x.is_active} for x in rows]

@router.post("/stages/{stage_id}/maps")
async def upload_map(stage_id: uuid.UUID, file: UploadFile=File(...), db:Session=Depends(get_db), _:User=Depends(require_permission("projects.manage"))):
    stage=db.get(ProjectStage,stage_id)
    if not stage: raise HTTPException(404,"Etapa no encontrada")
    ext=Path(file.filename or "").suffix.lower()
    if ext not in {".jpg",".jpeg",".png",".webp",".pdf"}: raise HTTPException(400,"Formato de plano no permitido")
    folder=Path(settings.upload_path)/"plans"/str(stage_id); folder.mkdir(parents=True,exist_ok=True)
    current=db.scalar(select(func.max(StageMap.version)).where(StageMap.stage_id==stage_id)) or 0
    filename=f"{uuid.uuid4().hex}{ext}"; target=folder/filename
    target.write_bytes(await file.read())
    for old in db.scalars(select(StageMap).where(StageMap.stage_id==stage_id,StageMap.is_active.is_(True))).all(): old.is_active=False
    item=StageMap(stage_id=stage_id,name=file.filename or filename,file_path=f"plans/{stage_id}/{filename}",file_type=file.content_type or ext,version=current+1,is_active=True)
    db.add(item); db.commit(); db.refresh(item)
    return {"id":str(item.id),"name":item.name,"version":item.version,"is_active":item.is_active}

@router.get("/stages/{stage_id}/blocks")
def list_blocks(stage_id: uuid.UUID, db:Session=Depends(get_db), _:User=Depends(get_current_user)):
    rows=db.scalars(select(Block).where(Block.stage_id==stage_id,Block.active.is_(True)).order_by(Block.name)).all()
    return [{"id":str(x.id),"stage_id":str(x.stage_id),"name":x.name,"description":x.description} for x in rows]

@router.post("/stages/{stage_id}/blocks")
def create_block(stage_id: uuid.UUID,payload:BlockCreate,db:Session=Depends(get_db),_:User=Depends(require_permission("properties.manage"))):
    if not db.get(ProjectStage,stage_id): raise HTTPException(404,"Etapa no encontrada")
    b=Block(stage_id=stage_id,**payload.model_dump()); db.add(b)
    try: db.commit()
    except IntegrityError: db.rollback(); raise HTTPException(409,"Ya existe esa manzana en la etapa")
    db.refresh(b); return {"id":str(b.id),"stage_id":str(b.stage_id),"name":b.name,"description":b.description}

@router.get("/property-statuses")
def statuses(db:Session=Depends(get_db),_:User=Depends(get_current_user)):
    rows=db.scalars(select(PropertyStatus).where(PropertyStatus.active.is_(True)).order_by(PropertyStatus.sort_order)).all()
    return [{"id":str(x.id),"code":x.code,"name":x.name} for x in rows]

@router.get("/properties")
def properties(stage_id: uuid.UUID | None=None, status_code:str|None=None, db:Session=Depends(get_db), _:User=Depends(get_current_user)):
    stmt=select(Property).join(Block).join(PropertyStatus).order_by(Block.name,Property.lot_number)
    if stage_id: stmt=stmt.where(Block.stage_id==stage_id)
    if status_code: stmt=stmt.where(PropertyStatus.code==status_code)
    rows=db.scalars(stmt).unique().all()
    return [{"id":str(x.id),"code":x.code,"lot_number":x.lot_number,"block_id":str(x.block_id),"block":x.block.name,
        "stage_id":str(x.block.stage_id),"status":{"code":x.status.code,"name":x.status.name},
        "cadastral_key":x.cadastral_key,"area_m2":float(x.area_m2),"price_per_m2":float(x.price_per_m2) if x.price_per_m2 is not None else None,
        "total_price":float(x.total_price),"location_reference":x.location_reference,"notes":x.notes,"active":x.active} for x in rows]

@router.post("/properties")
def create_property(payload:PropertyCreate,request:Request,db:Session=Depends(get_db),current:User=Depends(require_permission("properties.manage"))):
    block=db.get(Block,uuid.UUID(payload.block_id))
    if not block: raise HTTPException(404,"Manzana no encontrada")
    status_obj=db.scalar(select(PropertyStatus).where(PropertyStatus.code==payload.status_code))
    if not status_obj: raise HTTPException(400,"Estado de predio inválido")
    data=payload.model_dump(exclude={"status_code","block_id"})
    if payload.price_per_m2 is not None:
        data["total_price"]=(payload.area_m2*payload.price_per_m2).quantize(Decimal("0.01"))
    p=Property(block_id=block.id,status_id=status_obj.id,**data); db.add(p)
    try:
        db.flush()
        audit(db,current,"PROPERTY_CREATE","property",p.id,{"code":p.code,"block_id":p.block_id,"lot_number":p.lot_number,"total_price":p.total_price,"status":status_obj.code},request)
        db.commit()
    except IntegrityError: db.rollback(); raise HTTPException(409,"Código o número de lote duplicado")
    db.refresh(p); return {"id":str(p.id),"code":p.code}


@router.put("/properties/{property_id}")
def update_property(property_id: uuid.UUID,payload:PropertyUpdate,request:Request,db:Session=Depends(get_db),current:User=Depends(require_permission("properties.manage"))):
    p=db.get(Property,property_id)
    if not p: raise HTTPException(404,"Predio no encontrado")
    block=db.get(Block,uuid.UUID(payload.block_id))
    if not block: raise HTTPException(404,"Manzana no encontrada")
    status_obj=db.scalar(select(PropertyStatus).where(PropertyStatus.code==payload.status_code))
    if not status_obj: raise HTTPException(400,"Estado de predio inválido")

    old={
        "code":p.code,"block_id":str(p.block_id),"lot_number":p.lot_number,
        "cadastral_key":p.cadastral_key,"area_m2":str(p.area_m2),
        "price_per_m2":str(p.price_per_m2) if p.price_per_m2 is not None else None,
        "total_price":str(p.total_price),"location_reference":p.location_reference,
        "notes":p.notes,"status":p.status.code,
    }
    data=payload.model_dump(exclude={"status_code","block_id","total_price"})
    for key,value in data.items(): setattr(p,key,value)
    p.block_id=block.id
    p.status_id=status_obj.id
    p.total_price=(payload.area_m2*payload.price_per_m2).quantize(Decimal("0.01"))

    try:
        db.flush()
        audit(db,current,"PROPERTY_UPDATE","property",p.id,{
            "old":old,
            "new":{"code":p.code,"block_id":str(p.block_id),"lot_number":p.lot_number,
                   "cadastral_key":p.cadastral_key,"area_m2":str(p.area_m2),
                   "price_per_m2":str(p.price_per_m2),"total_price":str(p.total_price),
                   "location_reference":p.location_reference,"notes":p.notes,
                   "status":status_obj.code}
        },request)
        db.commit()
    except IntegrityError:
        db.rollback(); raise HTTPException(409,"Código o número de lote duplicado")
    db.refresh(p)
    return {"id":str(p.id),"code":p.code}


@router.delete("/properties/{property_id}")
def delete_property(property_id: uuid.UUID,request:Request,db:Session=Depends(get_db),current:User=Depends(require_permission("properties.manage"))):
    p=db.get(Property,property_id)
    if not p: raise HTTPException(404,"Predio no encontrado")

    reservation_count=db.scalar(select(func.count(Reservation.id)).where(Reservation.property_id==property_id)) or 0
    sale_count=db.scalar(select(func.count(Sale.id)).where(Sale.property_id==property_id)) or 0
    if reservation_count or sale_count:
        raise HTTPException(
            409,
            "No se puede eliminar el predio porque tiene historial de reservas o ventas. Debe conservarse por trazabilidad."
        )

    snapshot={"code":p.code,"block_id":str(p.block_id),"lot_number":p.lot_number,"cadastral_key":p.cadastral_key}
    audit(db,current,"PROPERTY_DELETE","property",p.id,snapshot,request)
    db.delete(p)
    try:
        db.commit()
    except IntegrityError:
        db.rollback(); raise HTTPException(409,"No se puede eliminar el predio porque tiene información relacionada")
    return {"ok":True,"message":"Predio eliminado correctamente"}
