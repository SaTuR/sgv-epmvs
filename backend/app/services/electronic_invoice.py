from datetime import date
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models import ElectronicInvoice, Sale, SystemSetting

def sri_config_complete(row:SystemSetting|None):
    return bool(
        row and row.sri_enabled and row.sri_ruc and row.sri_business_name
        and row.sri_establishment_code and row.sri_emission_point
    )

def ensure_invoice_for_paid_sale(db:Session,sale:Sale):
    existing=db.scalar(select(ElectronicInvoice).where(ElectronicInvoice.sale_id==sale.id))
    if existing:
        return existing

    cfg=db.scalar(select(SystemSetting).limit(1).with_for_update())
    invoice=ElectronicInvoice(
        sale_id=sale.id,
        customer_id=sale.customer_id,
        property_id=sale.property_id,
        issue_date=date.today(),
        environment=(cfg.sri_environment if cfg else "TEST"),
        total=sale.sale_price,
        status="PENDING_CONFIG",
    )

    if sri_config_complete(cfg):
        seq=int(cfg.sri_invoice_sequence or 1)
        sequential=f"{seq:09d}"
        invoice.establishment_code=cfg.sri_establishment_code
        invoice.emission_point=cfg.sri_emission_point
        invoice.sequential=sequential
        invoice.document_number=f"{cfg.sri_establishment_code}-{cfg.sri_emission_point}-{sequential}"
        invoice.status="PENDING_XML"
        cfg.sri_invoice_sequence=seq+1

    db.add(invoice)
    db.flush()
    return invoice
