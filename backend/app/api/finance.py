import uuid
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from dateutil.relativedelta import relativedelta
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.api.deps import get_current_user, get_db, require_permission
from app.models import Customer, Installment, Payment, PaymentAllocation, Property, PropertyStatus, Reservation, Sale, User
from app.schemas.finance import PaymentCreate, ReservationCreate, SaleCreate
from app.services.audit import audit

router=APIRouter(prefix="/api",tags=["Ventas y cartera"])

def money(v): return Decimal(v).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

def prop_status(db:Session,code:str):
    s=db.scalar(select(PropertyStatus).where(PropertyStatus.code==code))
    if not s: raise HTTPException(500,"Estado de predio no configurado")
    return s

@router.get("/reservations")
def reservations(db:Session=Depends(get_db),_:User=Depends(get_current_user)):
    rows=db.scalars(select(Reservation).where(Reservation.active.is_(True)).order_by(Reservation.created_at.desc())).all()
    out=[]
    for r in rows:
        c=db.get(Customer,r.customer_id); p=db.get(Property,r.property_id)
        out.append({"id":str(r.id),"customer_id":str(r.customer_id),"customer":c.full_name if c else "",
          "property_id":str(r.property_id),"property":p.code if p else "","reservation_date":r.reservation_date,
          "expires_on":r.expires_on,"notes":r.notes})
    return out

@router.post("/reservations")
def create_reservation(payload:ReservationCreate,request:Request,db:Session=Depends(get_db),current:User=Depends(require_permission("sales.manage"))):
    customer=db.get(Customer,uuid.UUID(payload.customer_id)); prop=db.get(Property,uuid.UUID(payload.property_id))
    if not customer or not prop: raise HTTPException(404,"Cliente o predio no encontrado")
    if prop.status.code!="AVAILABLE": raise HTTPException(409,"El predio ya no está disponible")
    r=Reservation(customer_id=customer.id,property_id=prop.id,reservation_date=payload.reservation_date or date.today(),expires_on=payload.expires_on,notes=payload.notes)
    prop.status_id=prop_status(db,"RESERVED").id
    db.add(r); db.flush()
    audit(db,current,"RESERVATION_CREATE","reservation",r.id,{"customer_id":customer.id,"property_id":prop.id,"expires_on":r.expires_on},request)
    db.commit(); db.refresh(r)
    return {"id":str(r.id)}

@router.post("/reservations/{reservation_id}/cancel")
def cancel_reservation(reservation_id:uuid.UUID,request:Request,db:Session=Depends(get_db),current:User=Depends(require_permission("reservations.release"))):
    r=db.get(Reservation,reservation_id)
    if not r or not r.active: raise HTTPException(404,"Reserva no encontrada")
    r.active=False
    p=db.get(Property,r.property_id)
    if p and p.status.code=="RESERVED": p.status_id=prop_status(db,"AVAILABLE").id
    audit(db,current,"RESERVATION_CANCEL","reservation",r.id,{"property_id":r.property_id,"customer_id":r.customer_id},request)
    db.commit(); return {"ok":True}

@router.get("/sales")
def sales(db:Session=Depends(get_db),_:User=Depends(get_current_user)):
    rows=db.scalars(select(Sale).where(Sale.active.is_(True)).order_by(Sale.created_at.desc())).all()
    out=[]
    for s in rows:
        c=db.get(Customer,s.customer_id); p=db.get(Property,s.property_id)
        installment_paid=sum((i.paid_amount for i in s.installments),Decimal("0"))
        paid=s.down_payment+installment_paid
        total=sum((i.amount for i in s.installments),Decimal("0"))
        overdue=sum((i.amount-i.paid_amount for i in s.installments if i.due_date<date.today() and i.status!="PAID"),Decimal("0"))
        out.append({"id":str(s.id),"customer_id":str(s.customer_id),"customer":c.full_name if c else "",
          "property_id":str(s.property_id),"property":p.code if p else "","confirmation_date":s.confirmation_date,
          "sale_price":float(s.sale_price),"down_payment":float(s.down_payment),"financed_amount":float(s.financed_amount),
          "installment_count":s.installment_count,"paid":float(paid),"balance":float(total-installment_paid),"overdue":float(overdue)})
    return out

@router.post("/sales")
def create_sale(payload:SaleCreate,request:Request,db:Session=Depends(get_db),current:User=Depends(require_permission("sales.manage"))):
    customer=db.get(Customer,uuid.UUID(payload.customer_id)); prop=db.get(Property,uuid.UUID(payload.property_id))
    if not customer or not prop: raise HTTPException(404,"Cliente o predio no encontrado")
    if prop.status.code not in {"AVAILABLE","RESERVED"}: raise HTTPException(409,"El predio no puede confirmarse para compra")

    reservation=None
    if prop.status.code=="RESERVED":
        if not payload.reservation_id:
            raise HTTPException(409,"El predio está reservado y debe confirmarse desde su reserva activa")
        reservation=db.get(Reservation,uuid.UUID(payload.reservation_id))
        if not reservation or not reservation.active:
            raise HTTPException(409,"La reserva ya no está activa")
        if reservation.property_id!=prop.id or reservation.customer_id!=customer.id:
            raise HTTPException(409,"La reserva no corresponde al cliente y predio seleccionados")

    if payload.down_payment>payload.sale_price: raise HTTPException(400,"La entrada no puede superar el precio de venta")
    financed=money(payload.sale_price-payload.down_payment)
    sale=Sale(customer_id=customer.id,property_id=prop.id,reservation_id=reservation.id if reservation else None,
      confirmation_date=payload.confirmation_date or date.today(),sale_price=money(payload.sale_price),down_payment=money(payload.down_payment),
      financed_amount=financed,installment_count=payload.installment_count if financed>0 else 0,frequency=payload.frequency,first_due_date=payload.first_due_date,notes=payload.notes)
    if financed>0:
        base=money(financed/Decimal(payload.installment_count))
        total=Decimal("0")
        for n in range(1,payload.installment_count+1):
            amount=base if n<payload.installment_count else money(financed-total)
            due=payload.first_due_date+relativedelta(months=n-1)
            sale.installments.append(Installment(number=n,due_date=due,amount=amount,paid_amount=0,status="PENDING"))
            total+=amount
    prop.status_id=prop_status(db,"PAYING" if financed>0 else "PAID").id
    if reservation: reservation.active=False
    db.add(sale); db.flush()
    audit(db,current,"SALE_CONFIRM","sale",sale.id,{"customer_id":customer.id,"property_id":prop.id,"sale_price":sale.sale_price,"down_payment":sale.down_payment,"installment_count":sale.installment_count},request)
    db.commit(); db.refresh(sale)
    return {"id":str(sale.id)}

@router.get("/sales/{sale_id}/installments")
def installments(sale_id:uuid.UUID,db:Session=Depends(get_db),_:User=Depends(get_current_user)):
    rows=db.scalars(select(Installment).where(Installment.sale_id==sale_id).order_by(Installment.number)).all()
    today=date.today()
    return [{"id":str(i.id),"number":i.number,"due_date":i.due_date,"amount":float(i.amount),"paid_amount":float(i.paid_amount),
      "balance":float(i.amount-i.paid_amount),"status":"OVERDUE" if i.due_date<today and i.status!="PAID" else i.status} for i in rows]

@router.post("/payments")
def create_payment(payload:PaymentCreate,request:Request,db:Session=Depends(get_db),current:User=Depends(require_permission("payments.manage"))):
    sale=db.get(Sale,uuid.UUID(payload.sale_id))
    if not sale or not sale.active: raise HTTPException(404,"Venta no encontrada")
    remaining=money(payload.amount)
    installments=db.scalars(select(Installment).where(Installment.sale_id==sale.id,Installment.status!="PAID").order_by(Installment.due_date,Installment.number)).all()
    outstanding=sum((i.amount-i.paid_amount for i in installments),Decimal("0"))
    if remaining>outstanding: raise HTTPException(400,"El pago supera el saldo pendiente")
    payment=Payment(sale_id=sale.id,payment_date=payload.payment_date or date.today(),amount=remaining,payment_method=payload.payment_method,reference=payload.reference,notes=payload.notes)
    db.add(payment); db.flush()
    for i in installments:
        if remaining<=0: break
        due=i.amount-i.paid_amount
        applied=min(due,remaining)
        i.paid_amount=money(i.paid_amount+applied)
        i.status="PAID" if i.paid_amount>=i.amount else "PARTIAL"
        db.add(PaymentAllocation(payment_id=payment.id,installment_id=i.id,amount=money(applied)))
        remaining=money(remaining-applied)
    if all(i.status=="PAID" for i in db.scalars(select(Installment).where(Installment.sale_id==sale.id)).all()):
        prop=db.get(Property,sale.property_id); prop.status_id=prop_status(db,"PAID").id
    audit(db,current,"PAYMENT_CREATE","payment",payment.id,{"sale_id":sale.id,"amount":payment.amount,"payment_method":payment.payment_method,"reference":payment.reference},request)
    db.commit(); db.refresh(payment)
    return {"id":str(payment.id)}

@router.get("/payments")
def payments(db:Session=Depends(get_db),_:User=Depends(get_current_user)):
    rows=db.scalars(select(Payment).where(Payment.status=="POSTED").order_by(Payment.payment_date.desc(),Payment.created_at.desc())).all()
    out=[]
    for p in rows:
        sale=db.get(Sale,p.sale_id); c=db.get(Customer,sale.customer_id) if sale else None; prop=db.get(Property,sale.property_id) if sale else None
        out.append({"id":str(p.id),"payment_date":p.payment_date,"amount":float(p.amount),"payment_method":p.payment_method,
          "reference":p.reference,"sale_id":str(p.sale_id),"customer":c.full_name if c else "","property":prop.code if prop else ""})
    return out

@router.get("/accounts-receivable")
def accounts_receivable(db:Session=Depends(get_db),_:User=Depends(require_permission("receivables.view"))):
    sales_rows=db.scalars(select(Sale).where(Sale.active.is_(True))).all()
    today=date.today(); out=[]
    for s in sales_rows:
        ins=db.scalars(select(Installment).where(Installment.sale_id==s.id)).all()
        balance=sum((i.amount-i.paid_amount for i in ins),Decimal("0"))
        if balance<=0: continue
        overdue_items=[i for i in ins if i.due_date<today and i.status!="PAID"]
        overdue=sum((i.amount-i.paid_amount for i in overdue_items),Decimal("0"))
        next_due=min((i.due_date for i in ins if i.status!="PAID"),default=None)
        c=db.get(Customer,s.customer_id); p=db.get(Property,s.property_id)
        max_days=max(((today-i.due_date).days for i in overdue_items),default=0)
        out.append({"sale_id":str(s.id),"customer":c.full_name if c else "","identification":c.identification if c else "",
          "property":p.code if p else "","sale_price":float(s.sale_price),"balance":float(balance),"overdue":float(overdue),
          "overdue_installments":len(overdue_items),"next_due":next_due,"days_overdue":max_days})
    return sorted(out,key=lambda x:(-x["overdue"],x["customer"]))
