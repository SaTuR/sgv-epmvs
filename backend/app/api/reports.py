import csv
import io
import uuid
from datetime import date, datetime
from decimal import Decimal
from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.api.deps import get_current_user, get_db, require_permission
from app.models import Block, Customer, Installment, Payment, ProjectStage, Property, PropertyStatus, Sale, User

router=APIRouter(prefix="/api/reports",tags=["Reportes"])

def sale_stage_id(db:Session,sale:Sale):
    prop=db.get(Property,sale.property_id)
    block=db.get(Block,prop.block_id) if prop else None
    return block.stage_id if block else None

def csv_response(rows,headers,filename):
    buf=io.StringIO()
    w=csv.writer(buf)
    w.writerow(headers)
    for row in rows: w.writerow(row)
    return Response(
        content="\ufeff"+buf.getvalue(),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition":f'attachment; filename="{filename}"'}
    )

@router.get("/dashboard")
def dashboard(stage_id:uuid.UUID|None=None,db:Session=Depends(get_db),_:User=Depends(get_current_user)):
    props=db.scalars(select(Property).where(Property.active.is_(True))).all()
    if stage_id:
        props=[p for p in props if p.block.stage_id==stage_id]
    prop_ids={p.id for p in props}
    status_counts={}
    for p in props:
        status_counts[p.status.name]=status_counts.get(p.status.name,0)+1

    sales=db.scalars(select(Sale).where(Sale.active.is_(True))).all()
    sales=[s for s in sales if s.property_id in prop_ids]
    payments=db.scalars(select(Payment).where(Payment.status=="POSTED")).all()
    sale_ids={s.id for s in sales}
    payments=[p for p in payments if p.sale_id in sale_ids]

    total_value=sum((p.total_price for p in props),Decimal("0"))
    committed=sum((s.sale_price for s in sales),Decimal("0"))
    down_payments=sum((s.down_payment for s in sales),Decimal("0"))
    collections=sum((p.amount for p in payments),Decimal("0"))
    collected=down_payments+collections

    today=date.today()
    pending=Decimal("0"); overdue=Decimal("0")
    for s in sales:
        for i in s.installments:
            bal=i.amount-i.paid_amount
            if bal>0:
                pending+=bal
                if i.due_date<today: overdue+=bal

    paid_props=sum(1 for p in props if p.status.code in {"PAID","AWARDED"})
    confirmed=sum(1 for p in props if p.status.code in {"CONFIRMED","PAYING","PAID","AWARDED"})
    recovery=(float(collected/committed*100) if committed>0 else 0)

    monthly={}
    for p in payments:
        key=p.payment_date.strftime("%Y-%m")
        monthly[key]=monthly.get(key,Decimal("0"))+p.amount
    return {
        "totals":{
            "properties":len(props),"available":status_counts.get("Disponible",0),
            "reserved":status_counts.get("Reservado",0),"confirmed":confirmed,"paid":paid_props,
            "total_value":float(total_value),"committed_sales":float(committed),
            "collected":float(collected),"pending":float(pending),"overdue":float(overdue),
            "recovery_percentage":round(recovery,2)
        },
        "properties_by_status":[{"status":k,"count":v} for k,v in sorted(status_counts.items())],
        "collections_by_month":[{"month":k,"amount":float(v)} for k,v in sorted(monthly.items())[-12:]],
    }

@router.get("/properties")
def properties_report(stage_id:uuid.UUID|None=None,status_code:str|None=None,db:Session=Depends(get_db),_:User=Depends(require_permission("reports.view"))):
    props=db.scalars(select(Property).where(Property.active.is_(True))).all()
    out=[]
    for p in props:
        if stage_id and p.block.stage_id!=stage_id: continue
        if status_code and p.status.code!=status_code: continue
        stage=db.get(ProjectStage,p.block.stage_id)
        out.append({
            "code":p.code,"stage":stage.name if stage else "","block":p.block.name,"lot":p.lot_number,
            "area_m2":float(p.area_m2),"total_price":float(p.total_price),"status":p.status.name,
            "cadastral_key":p.cadastral_key or ""
        })
    return out

@router.get("/properties.csv")
def properties_csv(stage_id:uuid.UUID|None=None,status_code:str|None=None,db:Session=Depends(get_db),_:User=Depends(require_permission("reports.view"))):
    data=properties_report(stage_id,status_code,db,_)
    rows=[[x["code"],x["stage"],x["block"],x["lot"],x["area_m2"],x["total_price"],x["status"],x["cadastral_key"]] for x in data]
    return csv_response(rows,["Código","Etapa","Manzana","Lote","Área m²","Precio","Estado","Clave catastral"],"predios.csv")

@router.get("/collections")
def collections_report(
    date_from:date|None=None,date_to:date|None=None,stage_id:uuid.UUID|None=None,
    db:Session=Depends(get_db),_:User=Depends(require_permission("reports.view"))
):
    payments=db.scalars(select(Payment).where(Payment.status=="POSTED").order_by(Payment.payment_date.desc())).all()
    out=[]
    for p in payments:
        if date_from and p.payment_date<date_from: continue
        if date_to and p.payment_date>date_to: continue
        sale=db.get(Sale,p.sale_id)
        if not sale: continue
        if stage_id and sale_stage_id(db,sale)!=stage_id: continue
        c=db.get(Customer,sale.customer_id); prop=db.get(Property,sale.property_id)
        block=db.get(Block,prop.block_id); stage=db.get(ProjectStage,block.stage_id)
        out.append({"date":p.payment_date,"customer":c.full_name,"identification":c.identification,
            "stage":stage.name,"property":prop.code,"method":p.payment_method,"reference":p.reference or "",
            "amount":float(p.amount)})
    return out

@router.get("/collections.csv")
def collections_csv(date_from:date|None=None,date_to:date|None=None,stage_id:uuid.UUID|None=None,db:Session=Depends(get_db),_:User=Depends(require_permission("reports.view"))):
    data=collections_report(date_from,date_to,stage_id,db,_)
    rows=[[x["date"],x["customer"],x["identification"],x["stage"],x["property"],x["method"],x["reference"],x["amount"]] for x in data]
    return csv_response(rows,["Fecha","Cliente","Identificación","Etapa","Predio","Forma de pago","Referencia","Valor"],"recaudacion.csv")

@router.get("/receivables")
def receivables_report(stage_id:uuid.UUID|None=None,db:Session=Depends(get_db),_:User=Depends(require_permission("reports.view"))):
    sales=db.scalars(select(Sale).where(Sale.active.is_(True))).all()
    today=date.today(); out=[]
    for s in sales:
        if stage_id and sale_stage_id(db,s)!=stage_id: continue
        ins=db.scalars(select(Installment).where(Installment.sale_id==s.id)).all()
        balance=sum((i.amount-i.paid_amount for i in ins),Decimal("0"))
        if balance<=0: continue
        overdue_items=[i for i in ins if i.due_date<today and i.status!="PAID"]
        overdue=sum((i.amount-i.paid_amount for i in overdue_items),Decimal("0"))
        c=db.get(Customer,s.customer_id); prop=db.get(Property,s.property_id)
        block=db.get(Block,prop.block_id); stage=db.get(ProjectStage,block.stage_id)
        out.append({"customer":c.full_name,"identification":c.identification,"stage":stage.name,
          "block":block.name,"property":prop.code,"sale_price":float(s.sale_price),"balance":float(balance),
          "overdue":float(overdue),"overdue_installments":len(overdue_items),
          "next_due":min((i.due_date for i in ins if i.status!="PAID"),default=None)})
    return out

@router.get("/receivables.csv")
def receivables_csv(stage_id:uuid.UUID|None=None,db:Session=Depends(get_db),_:User=Depends(require_permission("reports.view"))):
    data=receivables_report(stage_id,db,_)
    rows=[[x["customer"],x["identification"],x["stage"],x["block"],x["property"],x["sale_price"],x["balance"],x["overdue"],x["overdue_installments"],x["next_due"] or ""] for x in data]
    return csv_response(rows,["Cliente","Identificación","Etapa","Manzana","Predio","Precio venta","Saldo","Vencido","Cuotas vencidas","Próximo vencimiento"],"cartera.csv")
