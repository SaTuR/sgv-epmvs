import uuid
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session
from fastapi.responses import FileResponse

from app.api.deps import get_db, require_permission
from app.models import Customer, ElectronicInvoice, Installment, Property, Sale, User
from app.services.audit import audit
from app.services.electronic_invoice import ensure_invoice_for_paid_sale, prepare_invoice_xml
from app.services.sri_signing import sign_invoice_xml
from app.services.sri_client import request_authorization, save_authorization_xml, send_receipt
from app.services.ride import generate_ride
from app.services.invoice_email import send_invoice_email
from app.models import PropertyStatus, SystemSetting

router=APIRouter(prefix="/api/electronic-invoices",tags=["Facturación electrónica"])

STATUS_LABELS={
    "PENDING_CONFIG":"Pendiente de configuración SRI",
    "PENDING_XML":"Pendiente de generar XML",
    "XML_GENERATED":"XML generado",
    "SIGNED":"Firmada",
    "SENT":"Recibida por el SRI",
    "AUTHORIZED":"Autorizada",
    "REJECTED":"Rechazada",
    "ERROR":"Error",
}

@router.post("/sales/{sale_id}/create")
def create_invoice_for_paid_sale(sale_id:uuid.UUID,request:Request,db:Session=Depends(get_db),current:User=Depends(require_permission("invoices.create"))):
    sale=db.get(Sale,sale_id)
    if not sale or not sale.active:
        raise HTTPException(404,"Venta no encontrada")

    prop=db.get(Property,sale.property_id)
    if not prop:
        raise HTTPException(404,"Predio no encontrado")

    existing=db.scalar(select(ElectronicInvoice).where(ElectronicInvoice.sale_id==sale.id))
    if existing:
        raise HTTPException(409,"La venta ya tiene una factura electrónica")

    installments=db.scalars(select(Installment).where(Installment.sale_id==sale.id)).all()
    installment_balance=sum((i.amount-i.paid_amount for i in installments),0)
    balance=installment_balance if installments else sale.financed_amount

    if balance>0 or prop.status.code!="PAID":
        raise HTTPException(409,"La factura solo puede generarse cuando el predio está totalmente pagado")

    invoice=ensure_invoice_for_paid_sale(db,sale)
    audit(db,current,"EINVOICE_CREATE_MANUAL","electronic_invoice",invoice.id,{
        "sale_id":sale.id,
        "property_id":sale.property_id,
        "status":invoice.status,
        "document_number":invoice.document_number,
    },request)
    db.commit();db.refresh(invoice)
    return {
        "id":str(invoice.id),
        "status":invoice.status,
        "status_label":STATUS_LABELS.get(invoice.status,invoice.status),
        "document_number":invoice.document_number,
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
            "sri_reception_response":x.sri_reception_response,
            "sri_authorization_response":x.sri_authorization_response,
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
        "signed_xml_path":x.signed_xml_path,
        "ride_path":x.ride_path,
        "authorization_xml_path":x.authorization_xml_path,
        "sri_reception_response":x.sri_reception_response,
        "sri_authorization_response":x.sri_authorization_response,
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


@router.post("/{invoice_id}/sign")
def sign_xml(invoice_id:uuid.UUID,request:Request,db:Session=Depends(get_db),current:User=Depends(require_permission("invoices.view"))):
    invoice=db.get(ElectronicInvoice,invoice_id)
    if not invoice:
        raise HTTPException(404,"Factura electrónica no encontrada")
    cfg=db.scalar(select(SystemSetting).limit(1))
    if not cfg:
        raise HTTPException(400,"Configuración SRI no encontrada")
    try:
        sign_invoice_xml(invoice,cfg)
        audit(db,current,"EINVOICE_SIGNED","electronic_invoice",invoice.id,{
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


@router.get("/{invoice_id}/signed-xml")
def download_signed_xml(invoice_id:uuid.UUID,db:Session=Depends(get_db),_:User=Depends(require_permission("invoices.view"))):
    invoice=db.get(ElectronicInvoice,invoice_id)
    if not invoice:
        raise HTTPException(404,"Factura electrónica no encontrada")
    if not invoice.signed_xml_path:
        raise HTTPException(404,"La factura todavía no tiene XML firmado")
    return FileResponse(
        invoice.signed_xml_path,
        media_type="application/xml",
        filename=f"{invoice.access_key or invoice.id}_signed.xml",
    )


@router.post("/{invoice_id}/send-sri")
def send_to_sri(invoice_id:uuid.UUID,request:Request,db:Session=Depends(get_db),current:User=Depends(require_permission("invoices.view"))):
    invoice=db.get(ElectronicInvoice,invoice_id)
    if not invoice:
        raise HTTPException(404,"Factura electrónica no encontrada")
    try:
        result=send_receipt(invoice)
        invoice.sri_reception_response=result["raw"]
        if result["state"]=="RECIBIDA":
            invoice.status="SENT"
            invoice.error_message=None
        else:
            invoice.status="REJECTED"
            invoice.error_message=" | ".join(result["messages"]) or "El SRI devolvió el comprobante."
        audit(db,current,"EINVOICE_SRI_RECEPTION","electronic_invoice",invoice.id,{
            "state":result["state"],
            "messages":result["messages"],
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
        "error_message":invoice.error_message,
    }


@router.post("/{invoice_id}/authorize")
def authorize_sri(invoice_id:uuid.UUID,request:Request,db:Session=Depends(get_db),current:User=Depends(require_permission("invoices.view"))):
    invoice=db.get(ElectronicInvoice,invoice_id)
    if not invoice:
        raise HTTPException(404,"Factura electrónica no encontrada")

    try:
        result=request_authorization(invoice)
        invoice.sri_authorization_response=result["raw"]

        if result["state"]=="AUTORIZADO":
            invoice.status="AUTHORIZED"
            invoice.authorization_number=result["authorization_number"]
            invoice.authorized_at=result["authorization_date"]
            target=save_authorization_xml(invoice,result)
            invoice.authorization_xml_path=str(target) if target else None

            prop=db.get(Property,invoice.property_id)
            invoiced_status=db.scalar(select(PropertyStatus).where(PropertyStatus.code=="INVOICED"))
            if not invoiced_status:
                raise ValueError("Estado de predio FACTURADO no configurado")
            if prop:
                prop.status_id=invoiced_status.id
            invoice.error_message=None

        elif result["state"]=="NO AUTORIZADO":
            invoice.status="REJECTED"
            invoice.error_message=" | ".join(result["messages"]) or "El SRI no autorizó el comprobante."
        else:
            invoice.status="SENT"
            invoice.error_message=" | ".join(result["messages"]) or "Autorización aún no disponible."

        audit(db,current,"EINVOICE_SRI_AUTHORIZATION","electronic_invoice",invoice.id,{
            "state":result["state"],
            "authorization_number":result["authorization_number"],
            "messages":result["messages"],
            "access_key":invoice.access_key,
        },request)
        db.commit();db.refresh(invoice)

    except ValueError as exc:
        db.rollback()
        raise HTTPException(400,str(exc))

    if invoice.status=="AUTHORIZED":
        cfg=db.scalar(select(SystemSetting).limit(1))
        customer=db.get(Customer,invoice.customer_id)
        prop=db.get(Property,invoice.property_id)
        sale=db.get(Sale,invoice.sale_id)

        if cfg and customer and prop and sale:
            try:
                generate_ride(invoice,cfg,customer,prop,sale)
                audit(db,current,"EINVOICE_RIDE_GENERATED","electronic_invoice",invoice.id,{"automatic":True},request)
                db.commit()
            except Exception as ride_exc:
                db.rollback()
                audit(db,current,"EINVOICE_RIDE_ERROR","electronic_invoice",invoice.id,{"automatic":True,"error":str(ride_exc)},request)
                db.commit()

        if cfg and customer and prop and cfg.invoice_email_enabled and cfg.invoice_email_send_on_authorization:
            try:
                send_invoice_email(invoice,cfg,customer,prop)
                audit(db,current,"EINVOICE_EMAIL_SENT","electronic_invoice",invoice.id,{"automatic":True,"to":customer.email},request)
                db.commit()
            except Exception as mail_exc:
                db.rollback()
                audit(db,current,"EINVOICE_EMAIL_ERROR","electronic_invoice",invoice.id,{"automatic":True,"error":str(mail_exc)},request)
                db.commit()

    return {
        "id":str(invoice.id),
        "status":invoice.status,
        "status_label":STATUS_LABELS.get(invoice.status,invoice.status),
        "authorization_number":invoice.authorization_number,
        "authorized_at":invoice.authorized_at,
        "error_message":invoice.error_message,
    }

@router.get("/{invoice_id}/authorized-xml")
def download_authorized_xml(invoice_id:uuid.UUID,db:Session=Depends(get_db),_:User=Depends(require_permission("invoices.view"))):
    invoice=db.get(ElectronicInvoice,invoice_id)
    if not invoice:
        raise HTTPException(404,"Factura electrónica no encontrada")
    if not invoice.authorization_xml_path:
        raise HTTPException(404,"La factura todavía no tiene XML autorizado")
    return FileResponse(
        invoice.authorization_xml_path,
        media_type="application/xml",
        filename=f"{invoice.access_key or invoice.id}_authorized.xml",
    )


@router.get("/{invoice_id}/ride.pdf")
def download_ride(invoice_id:uuid.UUID,db:Session=Depends(get_db),_:User=Depends(require_permission("invoices.view"))):
    invoice=db.get(ElectronicInvoice,invoice_id)
    if not invoice:
        raise HTTPException(404,"Factura electrónica no encontrada")
    if not invoice.ride_path:
        raise HTTPException(404,"La factura todavía no tiene RIDE generado")
    return FileResponse(invoice.ride_path,media_type="application/pdf",filename=f"RIDE_{invoice.document_number or invoice.id}.pdf")


@router.post("/{invoice_id}/generate-ride")
def regenerate_ride(invoice_id:uuid.UUID,request:Request,db:Session=Depends(get_db),current:User=Depends(require_permission("invoices.view"))):
    invoice=db.get(ElectronicInvoice,invoice_id)
    if not invoice:
        raise HTTPException(404,"Factura electrónica no encontrada")
    cfg=db.scalar(select(SystemSetting).limit(1))
    customer=db.get(Customer,invoice.customer_id)
    prop=db.get(Property,invoice.property_id)
    sale=db.get(Sale,invoice.sale_id)
    if not cfg or not customer or not prop or not sale:
        raise HTTPException(400,"No se encontraron los datos necesarios para generar el RIDE")
    try:
        generate_ride(invoice,cfg,customer,prop,sale)
        audit(db,current,"EINVOICE_RIDE_GENERATED","electronic_invoice",invoice.id,{"document_number":invoice.document_number},request)
        db.commit();db.refresh(invoice)
    except ValueError as exc:
        db.rollback();raise HTTPException(400,str(exc))
    return {"ok":True,"ride":True}


@router.post("/{invoice_id}/email")
def email_invoice(invoice_id:uuid.UUID,request:Request,db:Session=Depends(get_db),current:User=Depends(require_permission("invoices.view"))):
    invoice=db.get(ElectronicInvoice,invoice_id)
    if not invoice:
        raise HTTPException(404,"Factura electrónica no encontrada")
    if invoice.status!="AUTHORIZED":
        raise HTTPException(409,"Solo se puede enviar por correo una factura autorizada")
    cfg=db.scalar(select(SystemSetting).limit(1))
    customer=db.get(Customer,invoice.customer_id)
    prop=db.get(Property,invoice.property_id)
    sale=db.get(Sale,invoice.sale_id)
    if not cfg or not customer or not prop or not sale:
        raise HTTPException(400,"No se encontraron los datos necesarios para enviar la factura")
    try:
        if cfg.invoice_email_attach_ride and not invoice.ride_path:
            generate_ride(invoice,cfg,customer,prop,sale)
        send_invoice_email(invoice,cfg,customer,prop)
        audit(db,current,"EINVOICE_EMAIL_SENT","electronic_invoice",invoice.id,{"automatic":False,"to":customer.email},request)
        db.commit()
    except ValueError as exc:
        db.rollback();raise HTTPException(400,str(exc))
    return {"ok":True,"message":"Factura enviada por correo correctamente"}
