import uuid
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.api.deps import get_db, require_any_permission, require_permission
from app.models import Customer, Property, Sale, SaleCommission, Seller, User
from app.schemas.commercial import CommissionStatusUpdate, SellerCreate, SellerUpdate
from app.services.audit import audit

router=APIRouter(prefix="/api",tags=["Vendedores y comisiones"])

def money(v):
    return Decimal(v).quantize(Decimal("0.01"),rounding=ROUND_HALF_UP)

@router.get("/sellers")
def list_sellers(active_only:bool=False,db:Session=Depends(get_db),_:User=Depends(require_any_permission("sellers.view","sales.manage","reports.view"))):
    stmt=select(Seller).order_by(Seller.last_name,Seller.first_name)
    if active_only:
        stmt=stmt.where(Seller.active.is_(True))
    rows=db.scalars(stmt).all()
    return [{
        "id":str(s.id),"identification":s.identification,"first_name":s.first_name,"last_name":s.last_name,
        "full_name":s.full_name,"phone":s.phone,"email":s.email,"seller_type":s.seller_type,
        "default_commission_rate":float(s.default_commission_rate),"active":s.active
    } for s in rows]

@router.post("/sellers")
def create_seller(payload:SellerCreate,request:Request,db:Session=Depends(get_db),current:User=Depends(require_permission("sellers.manage"))):
    if db.scalar(select(Seller).where(Seller.identification==payload.identification.strip())):
        raise HTTPException(409,"Ya existe un vendedor con esa identificación")
    seller=Seller(
        identification=payload.identification.strip(),first_name=payload.first_name.strip(),last_name=payload.last_name.strip(),
        phone=(payload.phone or "").strip() or None,email=str(payload.email) if payload.email else None,
        seller_type=payload.seller_type,default_commission_rate=payload.default_commission_rate,active=True
    )
    db.add(seller);db.flush()
    audit(db,current,"SELLER_CREATE","seller",seller.id,{"identification":seller.identification,"name":seller.full_name,"rate":str(seller.default_commission_rate)},request)
    db.commit();db.refresh(seller)
    return {"id":str(seller.id)}

@router.put("/sellers/{seller_id}")
def update_seller(seller_id:uuid.UUID,payload:SellerUpdate,request:Request,db:Session=Depends(get_db),current:User=Depends(require_permission("sellers.manage"))):
    seller=db.get(Seller,seller_id)
    if not seller: raise HTTPException(404,"Vendedor no encontrado")
    other=db.scalar(select(Seller).where(Seller.identification==payload.identification.strip(),Seller.id!=seller.id))
    if other: raise HTTPException(409,"Ya existe otro vendedor con esa identificación")
    old={"identification":seller.identification,"name":seller.full_name,"rate":str(seller.default_commission_rate),"active":seller.active}
    seller.identification=payload.identification.strip();seller.first_name=payload.first_name.strip();seller.last_name=payload.last_name.strip()
    seller.phone=(payload.phone or "").strip() or None;seller.email=str(payload.email) if payload.email else None
    seller.seller_type=payload.seller_type;seller.default_commission_rate=payload.default_commission_rate;seller.active=payload.active
    audit(db,current,"SELLER_UPDATE","seller",seller.id,{"old":old,"new":{"identification":seller.identification,"name":seller.full_name,"rate":str(seller.default_commission_rate),"active":seller.active}},request)
    db.commit()
    return {"ok":True}

@router.get("/commissions")
def list_commissions(db:Session=Depends(get_db),_:User=Depends(require_permission("commissions.view"))):
    rows=db.scalars(select(SaleCommission).order_by(SaleCommission.created_at.desc())).all()
    out=[]
    for c in rows:
        sale=db.get(Sale,c.sale_id);seller=db.get(Seller,c.seller_id)
        customer=db.get(Customer,sale.customer_id) if sale else None
        prop=db.get(Property,sale.property_id) if sale else None
        out.append({
            "id":str(c.id),"sale_id":str(c.sale_id),"seller_id":str(c.seller_id),
            "seller":seller.full_name if seller else "","customer":customer.full_name if customer else "",
            "property":prop.code if prop else "","sale_price":float(sale.sale_price) if sale else 0,
            "commission_base":float(c.commission_base),"commission_rate":float(c.commission_rate),
            "commission_amount":float(c.commission_amount),"status":c.status,
            "approved_at":c.approved_at,"paid_at":c.paid_at,"payment_reference":c.payment_reference,"notes":c.notes
        })
    return out

@router.put("/commissions/{commission_id}/status")
def update_commission_status(commission_id:uuid.UUID,payload:CommissionStatusUpdate,request:Request,db:Session=Depends(get_db),current:User=Depends(require_permission("commissions.manage"))):
    row=db.get(SaleCommission,commission_id)
    if not row: raise HTTPException(404,"Comisión no encontrada")
    old=row.status
    if payload.status=="APPROVED":
        if "commissions.approve" not in {p.code for r in current.roles for p in r.permissions} and "system.admin" not in {p.code for r in current.roles for p in r.permissions}:
            raise HTTPException(403,"No tiene permiso para aprobar comisiones")
        row.approved_at=datetime.now(timezone.utc);row.approved_by=current.id
    elif payload.status=="PAID":
        if "commissions.pay" not in {p.code for r in current.roles for p in r.permissions} and "system.admin" not in {p.code for r in current.roles for p in r.permissions}:
            raise HTTPException(403,"No tiene permiso para registrar pago de comisiones")
        if not payload.payment_reference or not payload.payment_reference.strip():
            raise HTTPException(400,"La referencia del pago de comisión es obligatoria")
        row.paid_at=datetime.now(timezone.utc);row.payment_reference=payload.payment_reference.strip()
    elif payload.status=="CANCELLED":
        row.paid_at=None
    row.status=payload.status;row.notes=payload.notes
    audit(db,current,"COMMISSION_STATUS_UPDATE","sale_commission",row.id,{"old":old,"new":row.status,"payment_reference":row.payment_reference},request)
    db.commit()
    return {"ok":True}
