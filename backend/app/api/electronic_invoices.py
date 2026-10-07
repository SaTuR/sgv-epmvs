import uuid
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session
from fastapi.responses import FileResponse

from app.api.deps import get_db, require_permission
from app.models import Customer, ElectronicInvoice, Property, Sale, User
from app.services.audit import audit
from app.services.electronic_invoice import prepare_invoice_xml

router=APIRouter(prefix="/api/electronic-invoices",tags=["Facturación electrónica"])

STATUS_LABELS={
    "PENDING_CONFIG":"Pendiente de configuración SRI",
    "PENDING_XML":"Pendiente de generar XML",
    "XML_GENERATED":"XML generado",
    "SIGNED":"Firmada",
    "SENT":"Enviada al SRI",
    "AUTHORIZED":"Autorizada",
    "REJECTED":"Rechazada",
    "ERROR":"Error",
}

@router.get("")
def list_invoices(db:Session=Depends(get_db),_:User=Depends(require_permission("invoices.view"))):
    rows=db.scalars(select(ElectronicInvoice).order_by(ElectronicInvoice.created_at.desc())).all()
    out=[]
    for x in rows:
        sale=db.get(Sale,x.sale_id)
        customer=db.get(Customer,x.customer_id)
        prop=db.get(Property,x.property_id)
        out.append({
            "id":str(x.id),
            "sale_id":str(x.sale_id),
            "issue_date":x.issue_date,
            "customer":customer.full_name if customer else "",
            "identification":customer.identification if customer else "",
            "property":prop.code if prop else "",
            "total":float(x.total),
            "environment":x.environment,
            "document_number":x.document_number,
            "status":x.status,
            "status_label":STATUS_LABELS.get(x.status,x.status),
            "authorization_number":x.authorization_number,
            "authorized_at":x.authorized_at,
            "error_message":x.error_message,
        })
    return out

@router.get("/{invoice_id}")
def invoice_detail(invoice_id:uuid.UUID,db:Session=Depends(get_db),_:User=Depends(require_permission("invoices.view"))):
    x=db.get(ElectronicInvoice,invoice_id)
    if not x: raise HTTPException(404,"Factura electrónica no encontrada")
    return {
        "id":str(x.id),
        "sale_id":str(x.sale_id),
        "customer_id":str(x.customer_id),
        "property_id":str(x.property_id),
        "issue_date":x.issue_date,
        "environment":x.environment,
        "establishment_code":x.establishment_code,
        "emission_point":x.emission_point,
        "sequential":x.sequential,
        "document_number":x.document_number,
        "status":x.status,
        "status_label":STATUS_LABELS.get(x.status,x.status),
        "total":float(x.total),
        "access_key":x.access_key,
        "authorization_number":x.authorization_number,
        "authorized_at":x.authorized_at,
        "xml_path":x.xml_path,
        "ride_path":x.ride_path,
        "error_message":x.error_message,
    }


@router.post("/{invoice_id}/generate-xml")
def generate_xml(invoice_id:uuid.UUID,request:Request,db:Session=Depends(get_db),current:User=Depends(require_permission("invoices.view"))):
    invoice=db.get(ElectronicInvoice,invoice_id)
    if not invoice:
        raise HTTPException(404,"Factura electrónica no encontrada")
    if invoice.status in {"SIGNED","SENT","AUTHORIZED"}:
        raise HTTPException(409,"La factura ya avanzó a una etapa posterior y no puede regenerarse")
    try:
        prepare_invoice_xml(db,invoice)
        audit(db,current,"EINVOICE_XML_GENERATED","electronic_invoice",invoice.id,{
            "sale_id":invoice.sale_id,
            "document_number":invoice.document_number,
            "access_key":invoice.access_key,
        },request)
        db.commit();db.refresh(invoice)
    except ValueError as exc:
        db.rollback()
        raise HTTPException(400,str(exc))
    return {
        "id":str(invoice.id),
        "status":invoice.status,
        "status_label":STATUS_LABELS.get(invoice.status,invoice.status),
        "document_number":invoice.document_number,
        "access_key":invoice.access_key,
    }


@router.get("/{invoice_id}/xml")
def download_xml(invoice_id:uuid.UUID,db:Session=Depends(get_db),_:User=Depends(require_permission("invoices.view"))):
    invoice=db.get(ElectronicInvoice,invoice_id)
    if not invoice:
        raise HTTPException(404,"Factura electrónica no encontrada")
    if not invoice.xml_path:
        raise HTTPException(404,"La factura todavía no tiene XML generado")
    return FileResponse(
        invoice.xml_path,
        media_type="application/xml",
        filename=f"{invoice.access_key or invoice.id}.xml",
    )
