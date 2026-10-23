from __future__ import annotations

import hashlib
from datetime import date
from decimal import Decimal
from pathlib import Path
from xml.etree import ElementTree as ET

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings as app_settings
from app.models import Customer, ElectronicInvoice, Property, Sale, SystemSetting


INVOICE_DOC_CODE="01"
NORMAL_EMISSION="1"

def modulo11(value:str)->str:
    total=0
    factor=2
    for digit in reversed(value):
        total+=int(digit)*factor
        factor+=1
        if factor>7:
            factor=2
    result=11-(total%11)
    if result==11:
        return "0"
    if result==10:
        return "1"
    return str(result)


def numeric_code(invoice:ElectronicInvoice)->str:
    seed=f"{invoice.sale_id}:{invoice.document_number}:{invoice.issue_date.isoformat()}"
    number=int(hashlib.sha256(seed.encode("utf-8")).hexdigest()[:16],16)%100_000_000
    return f"{number:08d}"


def environment_code(environment:str)->str:
    return "2" if environment=="PRODUCTION" else "1"


def build_access_key(invoice:ElectronicInvoice,ruc:str)->str:
    if not invoice.establishment_code or not invoice.emission_point or not invoice.sequential:
        raise ValueError("La factura no tiene establecimiento, punto de emisión o secuencial")
    base=(
        invoice.issue_date.strftime("%d%m%Y")
        +INVOICE_DOC_CODE
        +ruc
        +environment_code(invoice.environment)
        +invoice.establishment_code
        +invoice.emission_point
        +invoice.sequential
        +numeric_code(invoice)
        +NORMAL_EMISSION
    )
    if len(base)!=48 or not base.isdigit():
        raise ValueError("No fue posible conformar los 48 dígitos base de la clave de acceso")
    return base+modulo11(base)


def sri_config_complete(row:SystemSetting|None):
    return bool(
        row and row.sri_enabled and row.sri_ruc and row.sri_business_name
        and row.sri_establishment_code and row.sri_emission_point
    )

def sri_billing_ready(row:SystemSetting|None)->tuple[bool,list[str]]:
    missing=[]
    if not row:
        return False,["configuración SRI"]
    if not row.sri_enabled: missing.append("facturación electrónica activada")
    if not row.sri_ruc: missing.append("RUC")
    if not row.sri_business_name: missing.append("razón social")
    if not row.sri_establishment_code: missing.append("establecimiento")
    if not row.sri_emission_point: missing.append("punto de emisión")
    if not row.sri_tax_code: missing.append("código de impuesto")
    if not row.sri_tax_percentage_code: missing.append("código de porcentaje")
    if not row.sri_payment_method_code: missing.append("forma de pago SRI")
    if not row.sri_certificate_path or not row.sri_certificate_password_encrypted:
        missing.append("certificado de firma electrónica")
    elif not Path(row.sri_certificate_path).is_file():
        missing.append("archivo del certificado de firma electrónica")
    return len(missing)==0,missing


def allocate_number(db:Session,invoice:ElectronicInvoice,cfg:SystemSetting)->None:
    if invoice.sequential and invoice.document_number:
        return
    seq=int(cfg.sri_invoice_sequence or 1)
    if seq<1 or seq>999_999_999:
        raise ValueError("El secuencial SRI configurado está fuera de rango")

    establishment=cfg.sri_establishment_code
    emission_point=cfg.sri_emission_point
    while seq<=999_999_999:
        sequential=f"{seq:09d}"
        document_number=f"{establishment}-{emission_point}-{sequential}"
        exists=db.scalar(
            select(ElectronicInvoice.id).where(
                ElectronicInvoice.document_number==document_number
            )
        )
        if not exists:
            invoice.establishment_code=establishment
            invoice.emission_point=emission_point
            invoice.sequential=sequential
            invoice.document_number=document_number
            cfg.sri_invoice_sequence=seq+1
            return
        seq+=1

    raise ValueError("No existen secuenciales SRI disponibles para el establecimiento y punto de emisión configurados.")


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
        allocate_number(db,invoice,cfg)
        invoice.status="PENDING_XML"

    db.add(invoice)
    db.flush()
    return invoice


def buyer_identification_code(customer:Customer)->str:
    mapping={
        "RUC":"04",
        "CEDULA":"05",
        "PASAPORTE":"06",
        "CONSUMIDOR_FINAL":"07",
        "EXTERIOR":"08",
    }
    return mapping.get((customer.identification_type or "").upper(),"05")


def money(value:Decimal|int|float)->str:
    return f"{Decimal(value):.2f}"


def sub(parent:ET.Element,name:str,value=None)->ET.Element:
    node=ET.SubElement(parent,name)
    if value is not None:
        node.text=str(value)
    return node


def build_invoice_xml(db:Session,invoice:ElectronicInvoice,cfg:SystemSetting)->bytes:
    sale=db.get(Sale,invoice.sale_id)
    customer=db.get(Customer,invoice.customer_id)
    prop=db.get(Property,invoice.property_id)
    if not sale or not customer or not prop:
        raise ValueError("No se encontraron los datos de venta, cliente o predio")
    if not cfg.sri_ruc or not cfg.sri_business_name:
        raise ValueError("Configuración SRI incompleta")

    access_key=build_access_key(invoice,cfg.sri_ruc)
    invoice.access_key=access_key

    gross=Decimal(invoice.total)
    rate=Decimal(str(cfg.sri_tax_rate or 0))
    if rate>0 and cfg.sri_prices_include_tax:
        base=(gross/(Decimal("1")+(rate/Decimal("100")))).quantize(Decimal("0.01"))
        tax_value=(gross-base).quantize(Decimal("0.01"))
        grand_total=gross.quantize(Decimal("0.01"))
    elif rate>0:
        base=gross.quantize(Decimal("0.01"))
        tax_value=(base*rate/Decimal("100")).quantize(Decimal("0.01"))
        grand_total=(base+tax_value).quantize(Decimal("0.01"))
    else:
        base=gross.quantize(Decimal("0.01"))
        tax_value=Decimal("0.00")
        grand_total=gross.quantize(Decimal("0.01"))

    root=ET.Element("factura",{"id":"comprobante","version":"2.1.0"})
    trib=sub(root,"infoTributaria")
    sub(trib,"ambiente",environment_code(invoice.environment))
    sub(trib,"tipoEmision",NORMAL_EMISSION)
    sub(trib,"razonSocial",cfg.sri_business_name)
    if cfg.sri_trade_name:
        sub(trib,"nombreComercial",cfg.sri_trade_name)
    sub(trib,"ruc",cfg.sri_ruc)
    sub(trib,"claveAcceso",access_key)
    sub(trib,"codDoc",INVOICE_DOC_CODE)
    sub(trib,"estab",invoice.establishment_code)
    sub(trib,"ptoEmi",invoice.emission_point)
    sub(trib,"secuencial",invoice.sequential)
    sub(trib,"dirMatriz",cfg.address or "SAMBORONDON")

    info=sub(root,"infoFactura")
    sub(info,"fechaEmision",invoice.issue_date.strftime("%d/%m/%Y"))
    sub(info,"dirEstablecimiento",cfg.address or "SAMBORONDON")
    if cfg.sri_special_taxpayer_code:
        sub(info,"contribuyenteEspecial",cfg.sri_special_taxpayer_code)
    sub(info,"obligadoContabilidad","SI" if cfg.sri_accounting_required else "NO")
    sub(info,"tipoIdentificacionComprador",buyer_identification_code(customer))
    sub(info,"razonSocialComprador",customer.full_name)
    sub(info,"identificacionComprador",customer.identification)
    if customer.address:
        sub(info,"direccionComprador",customer.address)
    sub(info,"totalSinImpuestos",money(base))
    sub(info,"totalDescuento","0.00")

    taxes=sub(info,"totalConImpuestos")
    tax=sub(taxes,"totalImpuesto")
    sub(tax,"codigo",cfg.sri_tax_code)
    sub(tax,"codigoPorcentaje",cfg.sri_tax_percentage_code)
    sub(tax,"baseImponible",money(base))
    sub(tax,"valor",money(tax_value))
    sub(info,"propina","0.00")
    sub(info,"importeTotal",money(grand_total))
    sub(info,"moneda","DOLAR")

    pagos=sub(info,"pagos")
    pago=sub(pagos,"pago")
    sub(pago,"formaPago",cfg.sri_payment_method_code)
    sub(pago,"total",money(grand_total))

    detalles=sub(root,"detalles")
    detalle=sub(detalles,"detalle")
    sub(detalle,"codigoPrincipal",prop.code[:25])
    descripcion=f"Predio {prop.code}"
    if prop.cadastral_key:
        descripcion+=f" - Clave catastral {prop.cadastral_key}"
    sub(detalle,"descripcion",descripcion[:300])
    sub(detalle,"cantidad","1.000000")
    sub(detalle,"precioUnitario",money(base))
    sub(detalle,"descuento","0.00")
    sub(detalle,"precioTotalSinImpuesto",money(base))
    imp=sub(detalle,"impuestos")
    line_tax=sub(imp,"impuesto")
    sub(line_tax,"codigo",cfg.sri_tax_code)
    sub(line_tax,"codigoPorcentaje",cfg.sri_tax_percentage_code)
    sub(line_tax,"tarifa",money(rate))
    sub(line_tax,"baseImponible",money(base))
    sub(line_tax,"valor",money(tax_value))

    extras=[]
    if customer.email:
        extras.append(("Email",customer.email))
    if customer.mobile:
        extras.append(("Teléfono",customer.mobile))
    extras.append(("Predio",prop.code))
    if prop.cadastral_key:
        extras.append(("Clave catastral",prop.cadastral_key))
    provider_ruc=getattr(cfg,"sri_software_provider_ruc",None)
    if provider_ruc:
        extras.append(("RUC proveedor sistema facturación electrónica",provider_ruc))

    if extras:
        additional=sub(root,"infoAdicional")
        for name,value in extras:
            field=ET.SubElement(additional,"campoAdicional",{"nombre":name[:300]})
            field.text=str(value)[:300]

    ET.indent(root,space="  ")
    return ET.tostring(root,encoding="utf-8",xml_declaration=True)


def prepare_invoice_xml(db:Session,invoice:ElectronicInvoice)->ElectronicInvoice:
    cfg=db.scalar(select(SystemSetting).limit(1).with_for_update())
    if not sri_config_complete(cfg):
        raise ValueError("Configuración SRI incompleta o facturación electrónica desactivada")

    invoice.environment=cfg.sri_environment
    allocate_number(db,invoice,cfg)
    xml_bytes=build_invoice_xml(db,invoice,cfg)

    root=Path(app_settings.upload_path)/"electronic_invoices"/str(invoice.issue_date.year)
    root.mkdir(parents=True,exist_ok=True)
    path=root/f"{invoice.access_key}.xml"
    path.write_bytes(xml_bytes)

    invoice.xml_path=str(path)
    invoice.status="XML_GENERATED"
    invoice.error_message=None
    db.flush()
    return invoice
