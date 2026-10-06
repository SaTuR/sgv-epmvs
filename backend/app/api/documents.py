import uuid
from datetime import date, datetime
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy import select, text
from sqlalchemy.orm import Session
from app.api.deps import get_current_user, get_db, require_any_permission, require_permission
from app.config import settings
from app.models import Block, Customer, Installment, IssuedDocument, Payment, Project, ProjectStage, Property, Sale, SystemSetting, User
from app.services.pdf_documents import account_statement, payment_receipt, payments_certificate

router=APIRouter(prefix="/api",tags=["Documentos"])

PREFIX={"PAYMENT_RECEIPT":"CP","ACCOUNT_STATEMENT":"EC","PAYMENTS_CERTIFICATE":"CERT"}

def get_or_issue(db:Session,doc_type:str,user:User,sale_id=None,payment_id=None):
    stmt=select(IssuedDocument).where(IssuedDocument.document_type==doc_type)
    stmt=stmt.where(IssuedDocument.payment_id==payment_id) if payment_id else stmt.where(IssuedDocument.sale_id==sale_id)
    existing=db.scalar(stmt)
    if existing: return existing
    seq=db.scalar(text("SELECT nextval('sgv_document_number_seq')"))
    number=f"{PREFIX[doc_type]}-{datetime.now():%Y}-{seq:06d}"
    item=IssuedDocument(document_type=doc_type,document_number=number,sale_id=sale_id,payment_id=payment_id,created_by=user.id)
    db.add(item);db.commit();db.refresh(item);return item

def sale_context(db:Session,sale:Sale,document:IssuedDocument,user:User):
    customer=db.get(Customer,sale.customer_id); prop=db.get(Property,sale.property_id)
    block=db.get(Block,prop.block_id); stage=db.get(ProjectStage,block.stage_id); project=db.get(Project,stage.project_id)
    installments=db.scalars(select(Installment).where(Installment.sale_id==sale.id).order_by(Installment.number)).all()
    payments=db.scalars(select(Payment).where(Payment.sale_id==sale.id,Payment.status=="POSTED").order_by(Payment.payment_date,Payment.created_at)).all()
    current_balance=sum((i.amount-i.paid_amount for i in installments),Decimal("0"))
    def status_label(i):
        if i.status=="PAID": return "Pagada"
        if i.status=="PARTIAL": return "Parcial"
        if i.due_date<date.today(): return "Vencida"
        return "Pendiente"
    system_setting=db.scalar(select(SystemSetting).limit(1))
    public_base_url=system_setting.public_base_url if system_setting else settings.public_base_url
    document_footer=system_setting.document_footer if system_setting else "Sistema de Gestión y Venta EPMVS"
    return {
        "document":document,"sale":sale,"customer":customer,"property":prop,"block_name":block.name,
        "stage_name":stage.name,"project_name":project.name,"installments":installments,"payments":payments,
        "current_balance":current_balance,"total_paid":sale.down_payment+sum((p.amount for p in payments),Decimal("0")),
        "status_label":status_label,"user_name":user.full_name,
        "verification_url":f"{public_base_url.rstrip('/')}/{document.verification_code}",
        "document_footer":document_footer,
    }

@router.get("/payments/{payment_id}/receipt.pdf")
def payment_pdf(payment_id:uuid.UUID,db:Session=Depends(get_db),user:User=Depends(require_any_permission("payments.manage","documents.view"))):
    payment=db.get(Payment,payment_id)
    if not payment or payment.status!="POSTED": raise HTTPException(404,"Pago no encontrado")
    sale=db.get(Sale,payment.sale_id)
    document=get_or_issue(db,"PAYMENT_RECEIPT",user,payment_id=payment.id)
    ctx=sale_context(db,sale,document,user)
    previous_payments=db.scalars(select(Payment).where(Payment.sale_id==sale.id,Payment.status=="POSTED",Payment.created_at<payment.created_at)).all()
    paid_before=sum((p.amount for p in previous_payments),Decimal("0"))
    ctx["payment"]=payment
    ctx["previous_balance"]=sale.financed_amount-paid_before
    ctx["balance_after"]=sale.financed_amount-paid_before-payment.amount
    pdf=payment_receipt(ctx)
    return Response(pdf,media_type="application/pdf",headers={"Content-Disposition":f'attachment; filename="{document.document_number}.pdf"'})

@router.get("/sales/{sale_id}/statement.pdf")
def statement_pdf(sale_id:uuid.UUID,db:Session=Depends(get_db),user:User=Depends(require_any_permission("sales.manage","documents.view"))):
    sale=db.get(Sale,sale_id)
    if not sale or not sale.active: raise HTTPException(404,"Compra no encontrada")
    document=get_or_issue(db,"ACCOUNT_STATEMENT",user,sale_id=sale.id)
    pdf=account_statement(sale_context(db,sale,document,user))
    return Response(pdf,media_type="application/pdf",headers={"Content-Disposition":f'attachment; filename="{document.document_number}.pdf"'})

@router.get("/sales/{sale_id}/payments-certificate.pdf")
def certificate_pdf(sale_id:uuid.UUID,db:Session=Depends(get_db),user:User=Depends(require_any_permission("sales.manage","documents.view"))):
    sale=db.get(Sale,sale_id)
    if not sale or not sale.active: raise HTTPException(404,"Compra no encontrada")
    document=get_or_issue(db,"PAYMENTS_CERTIFICATE",user,sale_id=sale.id)
    pdf=payments_certificate(sale_context(db,sale,document,user))
    return Response(pdf,media_type="application/pdf",headers={"Content-Disposition":f'attachment; filename="{document.document_number}.pdf"'})

@router.get("/public/documents/{verification_code}")
def verify_document(verification_code:uuid.UUID,db:Session=Depends(get_db)):
    d=db.scalar(select(IssuedDocument).where(IssuedDocument.verification_code==verification_code))
    if not d: raise HTTPException(404,"Documento no válido")
    return {"valid":True,"document_number":d.document_number,"document_type":d.document_type,"issued_at":d.created_at}


DOCUMENT_LABELS={
    "PAYMENT_RECEIPT":"Comprobante de pago",
    "ACCOUNT_STATEMENT":"Estado de cuenta",
    "PAYMENTS_CERTIFICATE":"Certificado de pagos",
}

@router.get("/documents")
def list_documents(
    q:str|None=None,
    document_type:str|None=None,
    db:Session=Depends(get_db),
    _:User=Depends(require_permission("documents.view")),
):
    rows=db.scalars(select(IssuedDocument).order_by(IssuedDocument.created_at.desc())).all()
    out=[]
    for d in rows:
        sale=db.get(Sale,d.sale_id) if d.sale_id else None
        payment=db.get(Payment,d.payment_id) if d.payment_id else None
        if not sale and payment: sale=db.get(Sale,payment.sale_id)
        customer=db.get(Customer,sale.customer_id) if sale else None
        prop=db.get(Property,sale.property_id) if sale else None
        item={
            "id":str(d.id),
            "document_type":d.document_type,
            "document_label":DOCUMENT_LABELS.get(d.document_type,d.document_type),
            "document_number":d.document_number,
            "verification_code":str(d.verification_code),
            "created_at":d.created_at,
            "customer":customer.full_name if customer else "",
            "identification":customer.identification if customer else "",
            "property":prop.code if prop else "",
            "sale_id":str(sale.id) if sale else None,
            "payment_id":str(payment.id) if payment else None,
        }
        if document_type and item["document_type"]!=document_type: continue
        if q:
            term=q.strip().lower()
            hay=" ".join([item["document_number"],item["customer"],item["identification"],item["property"]]).lower()
            if term not in hay: continue
        out.append(item)
    return out

@router.get("/documents/{document_id}/download.pdf")
def download_document(document_id:uuid.UUID,db:Session=Depends(get_db),user:User=Depends(require_permission("documents.view"))):
    d=db.get(IssuedDocument,document_id)
    if not d: raise HTTPException(404,"Documento no encontrado")
    if d.document_type=="PAYMENT_RECEIPT":
        payment=db.get(Payment,d.payment_id)
        sale=db.get(Sale,payment.sale_id) if payment else None
        if not payment or not sale: raise HTTPException(404,"Pago asociado no encontrado")
        ctx=sale_context(db,sale,d,user)
        previous_payments=db.scalars(select(Payment).where(Payment.sale_id==sale.id,Payment.status=="POSTED",Payment.created_at<payment.created_at)).all()
        paid_before=sum((p.amount for p in previous_payments),Decimal("0"))
        ctx["payment"]=payment
        ctx["previous_balance"]=sale.financed_amount-paid_before
        ctx["balance_after"]=sale.financed_amount-paid_before-payment.amount
        pdf=payment_receipt(ctx)
    elif d.document_type=="ACCOUNT_STATEMENT":
        sale=db.get(Sale,d.sale_id)
        if not sale: raise HTTPException(404,"Compra asociada no encontrada")
        pdf=account_statement(sale_context(db,sale,d,user))
    elif d.document_type=="PAYMENTS_CERTIFICATE":
        sale=db.get(Sale,d.sale_id)
        if not sale: raise HTTPException(404,"Compra asociada no encontrada")
        pdf=payments_certificate(sale_context(db,sale,d,user))
    else:
        raise HTTPException(400,"Tipo de documento no soportado")
    return Response(pdf,media_type="application/pdf",headers={"Content-Disposition":f'attachment; filename="{d.document_number}.pdf"'})
