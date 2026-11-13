import csv
import io
import uuid
from collections import defaultdict
from datetime import date, datetime
from decimal import Decimal
from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.orm import Session
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from app.api.deps import get_current_user, get_db, require_permission
from app.models import Block, Customer, ElectronicInvoice, Installment, Payment, ProjectStage, Property, PropertyStatus, Sale, SaleCommission, Seller, User
from app.services.report_pdfs import commissions_pdf

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
    customers_count=len(db.scalars(select(Customer).where(Customer.active.is_(True))).all())
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

    paid_props=sum(1 for p in props if p.status.code in {"PAID","INVOICED","AWARDED"})
    confirmed=sum(1 for p in props if p.status.code in {"CONFIRMED","PAYING","PAID","INVOICED","AWARDED"})
    recovery=(float(collected/committed*100) if committed>0 else 0)

    invoices=db.scalars(select(ElectronicInvoice)).all()
    invoices=[x for x in invoices if x.sale_id in sale_ids]
    invoice_sale_ids={x.sale_id for x in invoices}
    paid_pending_invoice=sum(1 for s in sales if s.property_id in prop_ids and db.get(Property,s.property_id).status.code=="PAID" and s.id not in invoice_sale_ids)
    invoices_in_process=sum(1 for x in invoices if x.status in {"PENDING_CONFIG","PENDING_XML","XML_GENERATED","SIGNED","SENT"})
    invoices_authorized=sum(1 for x in invoices if x.status=="AUTHORIZED")
    invoices_rejected=sum(1 for x in invoices if x.status in {"REJECTED","ERROR"})

    paid_pending_rows=[]
    for s in sales:
        prop=db.get(Property,s.property_id)
        if not prop or prop.status.code!="PAID" or s.id in invoice_sale_ids:
            continue
        customer=db.get(Customer,s.customer_id)
        paid_pending_rows.append({
            "sale_id":str(s.id),
            "property":prop.code,
            "customer":customer.full_name if customer else "",
            "sale_price":float(s.sale_price),
        })

    monthly={}
    for p in payments:
        key=p.payment_date.strftime("%Y-%m")
        monthly[key]=monthly.get(key,Decimal("0"))+p.amount
    return {
        "totals":{
            "customers":customers_count,
            "properties":len(props),"available":status_counts.get("Disponible",0),
            "reserved":status_counts.get("Reservado",0),"confirmed":confirmed,"paid":paid_props,
            "total_value":float(total_value),"committed_sales":float(committed),
            "collected":float(collected),"pending":float(pending),"overdue":float(overdue),
            "recovery_percentage":round(recovery,2),
            "paid_pending_invoice":paid_pending_invoice,
            "invoices_in_process":invoices_in_process,
            "invoices_authorized":invoices_authorized,
            "invoices_rejected":invoices_rejected
        },
        "properties_by_status":[{"status":k,"count":v} for k,v in sorted(status_counts.items())],
        "collections_by_month":[{"month":k,"amount":float(v)} for k,v in sorted(monthly.items())[-12:]],
        "paid_pending_invoices":paid_pending_rows[:20],
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

    sales=db.scalars(select(Sale).where(Sale.active.is_(True))).all()
    for s in sales:
        if s.down_payment<=0: continue
        down_date=s.down_payment_date or s.confirmation_date
        if date_from and down_date<date_from: continue
        if date_to and down_date>date_to: continue
        if stage_id and sale_stage_id(db,s)!=stage_id: continue
        c=db.get(Customer,s.customer_id); prop=db.get(Property,s.property_id)
        block=db.get(Block,prop.block_id); stage=db.get(ProjectStage,block.stage_id)
        out.append({"date":s.down_payment_date or s.confirmation_date,"customer":c.full_name,"identification":c.identification,
            "stage":stage.name,"property":prop.code,"method":s.down_payment_method or "ENTRADA",
            "reference":s.down_payment_reference or "",
            "bank_receipt":s.down_payment_bank_receipt or "",
            "amount":float(s.down_payment)})

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
            "bank_receipt":p.bank_receipt or "",
            "amount":float(p.amount)})
    return out

@router.get("/collections.csv")
def collections_csv(date_from:date|None=None,date_to:date|None=None,stage_id:uuid.UUID|None=None,db:Session=Depends(get_db),_:User=Depends(require_permission("reports.view"))):
    data=collections_report(date_from,date_to,stage_id,db,_)
    rows=[[x["date"],x["customer"],x["identification"],x["stage"],x["property"],x["method"],x["reference"],x["bank_receipt"],x["amount"]] for x in data]
    return csv_response(rows,["Fecha","Cliente","Identificación","Etapa","Predio","Forma de pago","Referencia interna","Comprobante bancario","Valor"],"recaudacion.csv")

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


COMMISSION_STATUS_LABELS={
    "PENDING":"Pendiente",
    "APPROVED":"Aprobada",
    "PAID":"Pagada",
    "CANCELLED":"Anulada",
}

def commission_detail_rows(
    db:Session,
    seller_id:uuid.UUID|None=None,
    status:str|None=None,
    stage_id:uuid.UUID|None=None,
    date_from:date|None=None,
    date_to:date|None=None,
):
    rows=db.scalars(select(SaleCommission).order_by(SaleCommission.created_at.desc())).all()
    out=[]
    for commission in rows:
        if seller_id and commission.seller_id!=seller_id: continue
        if status and status!="ALL" and commission.status!=status: continue
        sale=db.get(Sale,commission.sale_id)
        if not sale or not sale.active: continue
        if date_from and sale.confirmation_date<date_from: continue
        if date_to and sale.confirmation_date>date_to: continue
        prop=db.get(Property,sale.property_id)
        block=db.get(Block,prop.block_id) if prop else None
        stage=db.get(ProjectStage,block.stage_id) if block else None
        if stage_id and (not stage or stage.id!=stage_id): continue
        seller=db.get(Seller,commission.seller_id)
        customer=db.get(Customer,sale.customer_id)
        out.append({
            "id":str(commission.id),
            "sale_id":str(sale.id),
            "date":sale.confirmation_date,
            "seller_id":str(commission.seller_id),
            "seller":seller.full_name if seller else "",
            "customer":customer.full_name if customer else "",
            "identification":customer.identification if customer else "",
            "stage_id":str(stage.id) if stage else None,
            "stage":stage.name if stage else "",
            "property":prop.code if prop else "",
            "sale_price":float(sale.sale_price),
            "commission_base":float(commission.commission_base),
            "commission_rate":float(commission.commission_rate),
            "commission_amount":float(commission.commission_amount),
            "status":commission.status,
            "status_label":COMMISSION_STATUS_LABELS.get(commission.status,commission.status),
            "approved_at":commission.approved_at,
            "paid_at":commission.paid_at,
            "payment_reference":commission.payment_reference or "",
        })
    return out

def commission_summary_from_detail(detail):
    grouped={}
    totals={
        "sales_count":0,
        "sold_amount":0.0,
        "generated":0.0,
        "pending":0.0,
        "approved":0.0,
        "paid":0.0,
        "cancelled":0.0,
    }
    seen_sales=set()
    sold_by_seller=defaultdict(float)
    seen_sales_by_seller=defaultdict(set)

    for row in detail:
        sid=row["seller_id"]
        if sid not in grouped:
            grouped[sid]={
                "seller_id":sid,"seller":row["seller"],"sales_count":0,"sold_amount":0.0,
                "generated":0.0,"pending":0.0,"approved":0.0,"paid":0.0,"cancelled":0.0
            }
        g=grouped[sid]
        sale_key=row["sale_id"]
        if sale_key not in seen_sales_by_seller[sid]:
            seen_sales_by_seller[sid].add(sale_key)
            g["sales_count"]+=1
            g["sold_amount"]+=row["sale_price"]
        if row["status"]!="CANCELLED":
            g["generated"]+=row["commission_amount"]
        if row["status"]=="PENDING": g["pending"]+=row["commission_amount"]
        elif row["status"]=="APPROVED": g["approved"]+=row["commission_amount"]
        elif row["status"]=="PAID": g["paid"]+=row["commission_amount"]
        elif row["status"]=="CANCELLED": g["cancelled"]+=row["commission_amount"]

        if sale_key not in seen_sales:
            seen_sales.add(sale_key)
            totals["sales_count"]+=1
            totals["sold_amount"]+=row["sale_price"]
        if row["status"]!="CANCELLED":
            totals["generated"]+=row["commission_amount"]
        if row["status"]=="PENDING": totals["pending"]+=row["commission_amount"]
        elif row["status"]=="APPROVED": totals["approved"]+=row["commission_amount"]
        elif row["status"]=="PAID": totals["paid"]+=row["commission_amount"]
        elif row["status"]=="CANCELLED": totals["cancelled"]+=row["commission_amount"]

    sellers=sorted(grouped.values(),key=lambda x:(-x["generated"],x["seller"]))
    for row in sellers:
        for key in ("sold_amount","generated","pending","approved","paid","cancelled"):
            row[key]=round(row[key],2)
    for key in ("sold_amount","generated","pending","approved","paid","cancelled"):
        totals[key]=round(totals[key],2)
    return {"totals":totals,"sellers":sellers}

@router.get("/commissions")
def commissions_report(
    seller_id:uuid.UUID|None=None,status:str|None=None,stage_id:uuid.UUID|None=None,
    date_from:date|None=None,date_to:date|None=None,view:str="summary",
    db:Session=Depends(get_db),_:User=Depends(require_permission("reports.view"))
):
    detail=commission_detail_rows(db,seller_id,status,stage_id,date_from,date_to)
    if view=="detail":
        return {"totals":commission_summary_from_detail(detail)["totals"],"rows":detail}
    return commission_summary_from_detail(detail)

@router.get("/commissions.csv")
def commissions_csv(
    seller_id:uuid.UUID|None=None,status:str|None=None,stage_id:uuid.UUID|None=None,
    date_from:date|None=None,date_to:date|None=None,
    db:Session=Depends(get_db),_:User=Depends(require_permission("reports.view"))
):
    detail=commission_detail_rows(db,seller_id,status,stage_id,date_from,date_to)
    rows=[[x["date"],x["seller"],x["customer"],x["identification"],x["stage"],x["property"],x["sale_price"],x["commission_rate"],x["commission_amount"],x["status_label"],x["payment_reference"]] for x in detail]
    return csv_response(rows,["Fecha","Vendedor","Cliente","Identificación","Etapa","Predio","Venta","% Comisión","Comisión","Estado","Referencia pago"],"comisiones.csv")

@router.get("/commissions.xlsx")
def commissions_xlsx(
    seller_id:uuid.UUID|None=None,status:str|None=None,stage_id:uuid.UUID|None=None,
    date_from:date|None=None,date_to:date|None=None,
    db:Session=Depends(get_db),_:User=Depends(require_permission("reports.view"))
):
    detail=commission_detail_rows(db,seller_id,status,stage_id,date_from,date_to)
    summary=commission_summary_from_detail(detail)
    wb=Workbook()
    ws=wb.active
    ws.title="Resumen"
    headers=["Vendedor","Ventas","Valor vendido","Generada","Pendiente","Aprobada","Pagada","Anulada"]
    ws.append(headers)
    for cell in ws[1]:
        cell.font=Font(bold=True,color="FFFFFF")
        cell.fill=PatternFill("solid",fgColor="3A6C32")
        cell.alignment=Alignment(horizontal="center")
    for r in summary["sellers"]:
        ws.append([r["seller"],r["sales_count"],r["sold_amount"],r["generated"],r["pending"],r["approved"],r["paid"],r["cancelled"]])
    ws.append([])
    t=summary["totals"]
    ws.append(["TOTAL",t["sales_count"],t["sold_amount"],t["generated"],t["pending"],t["approved"],t["paid"],t["cancelled"]])

    wd=wb.create_sheet("Detalle")
    dheaders=["Fecha","Vendedor","Cliente","Identificación","Etapa","Predio","Venta","% Comisión","Comisión","Estado","Referencia pago"]
    wd.append(dheaders)
    for cell in wd[1]:
        cell.font=Font(bold=True,color="FFFFFF")
        cell.fill=PatternFill("solid",fgColor="3A6C32")
    for r in detail:
        wd.append([r["date"],r["seller"],r["customer"],r["identification"],r["stage"],r["property"],r["sale_price"],r["commission_rate"]/100,r["commission_amount"],r["status_label"],r["payment_reference"]])
    ws.freeze_panes="A2"
    wd.freeze_panes="A2"
    for row in ws.iter_rows(min_row=2,min_col=3,max_col=8):
        for cell in row: cell.number_format='$ #,##0.00'
    for row in wd.iter_rows(min_row=2,min_col=7,max_col=7):
        for cell in row: cell.number_format='$ #,##0.00'
    for row in wd.iter_rows(min_row=2,min_col=8,max_col=8):
        for cell in row: cell.number_format='0.00%'
    for row in wd.iter_rows(min_row=2,min_col=9,max_col=9):
        for cell in row: cell.number_format='$ #,##0.00'
    for sheet in (ws,wd):
        for col in sheet.columns:
            max_len=max(len(str(cell.value or "")) for cell in col)
            sheet.column_dimensions[col[0].column_letter].width=min(max(max_len+2,12),40)
    buf=io.BytesIO()
    wb.save(buf)
    return Response(
        content=buf.getvalue(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition":'attachment; filename="comisiones.xlsx"'}
    )

@router.get("/commissions.pdf")
def commissions_pdf_report(
    seller_id:uuid.UUID|None=None,status:str|None=None,stage_id:uuid.UUID|None=None,
    date_from:date|None=None,date_to:date|None=None,
    db:Session=Depends(get_db),_:User=Depends(require_permission("reports.view"))
):
    detail=commission_detail_rows(db,seller_id,status,stage_id,date_from,date_to)
    summary=commission_summary_from_detail(detail)
    filters=[]
    if seller_id:
        seller=db.get(Seller,seller_id);filters.append(f"Vendedor: {seller.full_name if seller else seller_id}")
    if status and status!="ALL": filters.append(f"Estado: {COMMISSION_STATUS_LABELS.get(status,status)}")
    if stage_id:
        stage=db.get(ProjectStage,stage_id);filters.append(f"Etapa: {stage.name if stage else stage_id}")
    if date_from: filters.append(f"Desde: {date_from}")
    if date_to: filters.append(f"Hasta: {date_to}")
    pdf=commissions_pdf(summary,detail," · ".join(filters) if filters else "Todos los registros")
    return Response(pdf,media_type="application/pdf",headers={"Content-Disposition":'attachment; filename="comisiones.pdf"'})

