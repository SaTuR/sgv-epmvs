import uuid
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from dateutil.relativedelta import relativedelta
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from app.api.deps import get_current_user, get_db, require_permission
from app.models import Customer, ElectronicInvoice, Installment, IssuedDocument, Payment, PaymentAllocation, Property, PropertyStatus, Reservation, Sale, SystemSetting, User
from app.schemas.finance import DownPaymentUpdate, InstallmentsUpdate, PaymentCreate, ReservationCreate, SaleCreate
from app.services.audit import audit
from app.services.electronic_invoice import sri_billing_ready

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
    cfg=db.scalar(select(SystemSetting).limit(1))
    sri_ready,_=sri_billing_ready(cfg)
    out=[]
    for s in rows:
        c=db.get(Customer,s.customer_id); p=db.get(Property,s.property_id)
        installment_paid=sum((i.paid_amount for i in s.installments),Decimal("0"))
        paid=s.down_payment+installment_paid
        total=sum((i.amount for i in s.installments),Decimal("0"))
        overdue=sum((i.amount-i.paid_amount for i in s.installments if i.due_date<date.today() and i.status!="PAID"),Decimal("0"))
        invoice=db.scalar(select(ElectronicInvoice).where(ElectronicInvoice.sale_id==s.id))
        payment_count=db.scalar(select(func.count(Payment.id)).where(Payment.sale_id==s.id)) or 0
        document_count=db.scalar(select(func.count(IssuedDocument.id)).where(IssuedDocument.sale_id==s.id)) or 0
        balance=money(total-installment_paid)
        out.append({"id":str(s.id),"customer_id":str(s.customer_id),"customer":c.full_name if c else "",
          "property_id":str(s.property_id),"property":p.code if p else "","property_status":p.status.code if p else "",
          "confirmation_date":s.confirmation_date,
          "sale_price":float(s.sale_price),"down_payment":float(s.down_payment),"financed_amount":float(s.financed_amount),
          "installment_count":s.installment_count,"paid":float(paid),"balance":float(balance),"overdue":float(overdue),
          "invoice_id":str(invoice.id) if invoice else None,
          "invoice_status":invoice.status if invoice else None,
          "can_generate_invoice":bool(sri_ready and p and p.status.code=="PAID" and balance<=0 and not invoice),
          "can_delete":bool(not invoice and payment_count==0 and document_count==0 and money(s.down_payment)==Decimal("0.00"))})
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

@router.delete("/sales/{sale_id}")
def delete_sale(sale_id:uuid.UUID,request:Request,db:Session=Depends(get_db),current:User=Depends(require_permission("system.admin"))):
    sale=db.get(Sale,sale_id)
    if not sale or not sale.active:
        raise HTTPException(404,"Compra no encontrada")

    invoice=db.scalar(select(ElectronicInvoice).where(ElectronicInvoice.sale_id==sale.id))
    payment_count=db.scalar(select(func.count(Payment.id)).where(Payment.sale_id==sale.id)) or 0
    document_count=db.scalar(select(func.count(IssuedDocument.id)).where(IssuedDocument.sale_id==sale.id)) or 0

    if invoice:
        raise HTTPException(409,"No se puede eliminar la compra porque ya tiene factura electrónica asociada")
    if payment_count>0 or money(sale.down_payment)>Decimal("0.00"):
        raise HTTPException(409,"No se puede eliminar la compra porque registra valores pagados")
    if document_count>0:
        raise HTTPException(409,"No se puede eliminar la compra porque tiene documentos emitidos")

    prop=db.get(Property,sale.property_id)
    audit(db,current,"SALE_DELETE","sale",sale.id,{
        "customer_id":str(sale.customer_id),
        "property_id":str(sale.property_id),
        "sale_price":str(sale.sale_price),
        "down_payment":str(sale.down_payment),
        "installment_count":sale.installment_count,
    },request)

    if prop:
        prop.status_id=prop_status(db,"AVAILABLE").id

    db.delete(sale)
    db.commit()
    return {"ok":True,"message":"Compra eliminada y predio liberado correctamente"}

@router.get("/sales/{sale_id}/installments")
def installments(sale_id:uuid.UUID,db:Session=Depends(get_db),_:User=Depends(get_current_user)):
    rows=db.scalars(select(Installment).where(Installment.sale_id==sale_id).order_by(Installment.number)).all()
    today=date.today()
    return [{"id":str(i.id),"number":i.number,"due_date":i.due_date,"amount":float(i.amount),"paid_amount":float(i.paid_amount),
      "balance":float(i.amount-i.paid_amount),"status":"OVERDUE" if i.due_date<today and i.status!="PAID" else i.status} for i in rows]

@router.put("/sales/{sale_id}/down-payment")
def update_down_payment(
    sale_id:uuid.UUID,
    payload:DownPaymentUpdate,
    request:Request,
    db:Session=Depends(get_db),
    current:User=Depends(require_permission("sales.manage"))
):
    sale=db.get(Sale,sale_id)
    if not sale or not sale.active:
        raise HTTPException(404,"Venta no encontrada")

    invoice=db.scalar(select(ElectronicInvoice).where(ElectronicInvoice.sale_id==sale.id))
    if invoice:
        raise HTTPException(409,"No se puede corregir la entrada porque la venta ya tiene factura electrónica asociada")

    new_down=money(payload.down_payment)
    if new_down>money(sale.sale_price):
        raise HTTPException(400,"La entrada no puede superar el precio de venta")

    rows=db.scalars(select(Installment).where(Installment.sale_id==sale.id).order_by(Installment.number)).all()
    financed=money(sale.sale_price-new_down)
    old_snapshot={
        "down_payment":str(sale.down_payment),
        "financed_amount":str(sale.financed_amount),
        "installments":[
            {"id":str(i.id),"number":i.number,"due_date":str(i.due_date),"amount":str(i.amount),"paid_amount":str(i.paid_amount)}
            for i in rows
        ],
    }

    if financed==Decimal("0.00"):
        if any(money(i.paid_amount)>Decimal("0.00") for i in rows):
            raise HTTPException(409,"No se puede llevar el financiado a cero porque ya existen pagos aplicados a cuotas")
        for i in rows:
            db.delete(i)
        sale.installment_count=0
    elif not rows:
        raise HTTPException(409,"La venta no tiene cuotas para redistribuir")
    elif payload.mode=="AUTO":
        base=money(financed/Decimal(len(rows)))
        running=Decimal("0.00")
        for idx,row in enumerate(rows):
            amount=base if idx<len(rows)-1 else money(financed-running)
            if amount<money(row.paid_amount):
                raise HTTPException(
                    409,
                    f"La redistribución automática dejaría la cuota #{row.number} por debajo de lo ya pagado. Use ajuste manual."
                )
            row.amount=amount
            running=money(running+amount)
            row.status="PAID" if money(row.paid_amount)>=amount else ("PARTIAL" if money(row.paid_amount)>0 else "PENDING")
    else:
        items=payload.installments or []
        if len(items)!=len(rows):
            raise HTTPException(400,"Para ajuste manual debe enviar todas las cuotas")
        current_by_id={str(i.id):i for i in rows}
        if {x.id for x in items}!=set(current_by_id.keys()):
            raise HTTPException(400,"La lista de cuotas no corresponde a esta venta")
        total=money(sum((money(x.amount) for x in items),Decimal("0.00")))
        if total!=financed:
            raise HTTPException(400,f"La suma de cuotas debe ser exactamente {financed:.2f}")
        for item in items:
            row=current_by_id[item.id]
            amount=money(item.amount)
            if amount<money(row.paid_amount):
                raise HTTPException(400,f"La cuota #{row.number} no puede ser menor a lo ya pagado")
            row.due_date=item.due_date
            row.amount=amount
            row.status="PAID" if money(row.paid_amount)>=amount else ("PARTIAL" if money(row.paid_amount)>0 else "PENDING")

    sale.down_payment=new_down
    sale.financed_amount=financed
    if financed>0:
        sale.installment_count=len(rows)

    prop=db.get(Property,sale.property_id)
    if prop:
        if financed==Decimal("0.00") or (rows and all(i.status=="PAID" for i in rows)):
            prop.status_id=prop_status(db,"PAID").id
        else:
            prop.status_id=prop_status(db,"PAYING").id

    audit(db,current,"DOWN_PAYMENT_UPDATE","sale",sale.id,{
        "old":old_snapshot,
        "new":{
            "down_payment":str(sale.down_payment),
            "financed_amount":str(sale.financed_amount),
            "mode":payload.mode,
            "installments":[
                {"id":str(i.id),"number":i.number,"due_date":str(i.due_date),"amount":str(i.amount),"paid_amount":str(i.paid_amount)}
                for i in rows
            ],
        },
    },request)
    db.commit()
    return {"ok":True,"message":"Entrada y plan de pagos actualizados correctamente"}

@router.put("/sales/{sale_id}/installments")
def update_installments(sale_id:uuid.UUID,payload:InstallmentsUpdate,request:Request,db:Session=Depends(get_db),current:User=Depends(require_permission("sales.manage"))):
    sale=db.get(Sale,sale_id)
    if not sale or not sale.active:
        raise HTTPException(404,"Venta no encontrada")

    current_rows=db.scalars(select(Installment).where(Installment.sale_id==sale.id).order_by(Installment.number)).all()
    current_by_id={str(i.id):i for i in current_rows}

    if len(payload.installments)!=len(current_rows):
        raise HTTPException(400,"Debe conservarse el mismo número de cuotas")

    sent_ids={x.id for x in payload.installments}
    if sent_ids!=set(current_by_id.keys()):
        raise HTTPException(400,"La lista de cuotas no corresponde a esta venta")

    new_total=money(sum((money(x.amount) for x in payload.installments),Decimal("0")))
    expected=money(sale.sale_price-sale.down_payment)
    if new_total!=expected:
        raise HTTPException(
            400,
            f"La suma de las cuotas debe ser exactamente {expected:.2f}. Entrada + cuotas debe ser igual al precio de venta {money(sale.sale_price):.2f}"
        )

    old=[]
    for item in payload.installments:
        row=current_by_id[item.id]
        new_amount=money(item.amount)
        if new_amount<money(row.paid_amount):
            raise HTTPException(
                400,
                f"La cuota #{row.number} no puede quedar en {new_amount:.2f} porque ya tiene {money(row.paid_amount):.2f} pagado"
            )
        old.append({"id":str(row.id),"number":row.number,"due_date":str(row.due_date),"amount":str(row.amount),"paid_amount":str(row.paid_amount)})
        row.due_date=item.due_date
        row.amount=new_amount
        if money(row.paid_amount)>=new_amount:
            row.status="PAID"
        elif money(row.paid_amount)>Decimal("0.00"):
            row.status="PARTIAL"
        else:
            row.status="PENDING"

    ordered=sorted(current_rows,key=lambda x:(x.due_date,x.number))
    sale.first_due_date=ordered[0].due_date
    sale.financed_amount=expected

    audit(db,current,"INSTALLMENTS_UPDATE","sale",sale.id,{
        "sale_price":str(sale.sale_price),
        "down_payment":str(sale.down_payment),
        "old":old,
        "new":[{"id":str(i.id),"number":i.number,"due_date":str(i.due_date),"amount":str(i.amount),"paid_amount":str(i.paid_amount)} for i in current_rows]
    },request)
    db.commit()
    return {"ok":True,"message":"Plan de pagos actualizado correctamente"}

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


@router.delete("/payments/{payment_id}")
def delete_payment(
    payment_id:uuid.UUID,
    request:Request,
    db:Session=Depends(get_db),
    current:User=Depends(require_permission("payments.delete"))
):
    payment=db.get(Payment,payment_id)
    if not payment or payment.status!="POSTED":
        raise HTTPException(404,"Pago no encontrado")

    sale=db.get(Sale,payment.sale_id)
    if not sale or not sale.active:
        raise HTTPException(409,"La venta asociada no está disponible")

    invoice=db.scalar(select(ElectronicInvoice).where(ElectronicInvoice.sale_id==sale.id))
    if invoice:
        raise HTTPException(409,"No se puede eliminar el pago porque la venta ya tiene factura electrónica asociada")

    allocations=db.scalars(
        select(PaymentAllocation).where(PaymentAllocation.payment_id==payment.id)
    ).all()

    snapshot=[]
    for allocation in allocations:
        installment=db.get(Installment,allocation.installment_id)
        if not installment:
            raise HTTPException(409,"El pago tiene asignaciones inconsistentes y no puede eliminarse automáticamente")

        new_paid=money(installment.paid_amount-allocation.amount)
        if new_paid<Decimal("0.00"):
            raise HTTPException(409,"La eliminación produciría un valor pagado negativo en una cuota")

        snapshot.append({
            "installment_id":str(installment.id),
            "installment_number":installment.number,
            "amount":str(allocation.amount),
            "paid_before":str(installment.paid_amount),
            "paid_after":str(new_paid),
        })

        installment.paid_amount=new_paid
        installment.status="PENDING" if new_paid<=0 else ("PARTIAL" if new_paid<installment.amount else "PAID")

    prop=db.get(Property,sale.property_id)
    all_installments=db.scalars(
        select(Installment).where(Installment.sale_id==sale.id)
    ).all()

    if prop:
        if all_installments and all(i.status=="PAID" for i in all_installments):
            prop.status_id=prop_status(db,"PAID").id
        elif sale.financed_amount>0:
            prop.status_id=prop_status(db,"PAYING").id

    audit(db,current,"PAYMENT_DELETE","payment",payment.id,{
        "sale_id":str(sale.id),
        "property_id":str(sale.property_id),
        "payment_date":str(payment.payment_date),
        "amount":str(payment.amount),
        "payment_method":payment.payment_method,
        "reference":payment.reference,
        "allocations":snapshot,
    },request)

    db.delete(payment)
    db.commit()
    return {"ok":True,"message":"Pago eliminado y cuotas recalculadas correctamente"}

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
