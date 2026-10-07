from __future__ import annotations

import io
from pathlib import Path

import qrcode
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, LETTER
from reportlab.lib.units import mm
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

from app.config import settings as app_settings
from app.models import Customer, ElectronicInvoice, Property, Sale, SystemSetting


def template_values(invoice:ElectronicInvoice,customer:Customer,prop:Property)->dict[str,str]:
    return {
        "customer_name":customer.full_name,
        "customer_identification":customer.identification,
        "document_number":invoice.document_number or "",
        "access_key":invoice.access_key or "",
        "authorization_number":invoice.authorization_number or "",
        "property_code":prop.code,
        "cadastral_key":prop.cadastral_key or "",
        "total":f"{invoice.total:.2f}",
        "issue_date":invoice.issue_date.strftime("%d/%m/%Y"),
        "authorized_at":invoice.authorized_at.strftime("%d/%m/%Y %H:%M") if invoice.authorized_at else "",
    }


def render_template(text:str|None,values:dict[str,str])->str:
    result=text or ""
    for key,value in values.items():
        result=result.replace("{"+key+"}",value)
    return result


def _hex(value:str,default="#3A6C32"):
    try:
        return colors.HexColor(value)
    except Exception:
        return colors.HexColor(default)


def generate_ride(invoice:ElectronicInvoice,cfg:SystemSetting,customer:Customer,prop:Property,sale:Sale)->Path:
    if invoice.status!="AUTHORIZED":
        raise ValueError("El RIDE solo puede generarse para una factura autorizada por el SRI.")

    values=template_values(invoice,customer,prop)
    root=Path(app_settings.upload_path)/"electronic_invoices"/str(invoice.issue_date.year)
    root.mkdir(parents=True,exist_ok=True)
    target=root/f"{invoice.access_key}_RIDE.pdf"

    pagesize=A4 if cfg.ride_page_size=="A4" else LETTER
    doc=SimpleDocTemplate(str(target),pagesize=pagesize,rightMargin=14*mm,leftMargin=14*mm,topMargin=12*mm,bottomMargin=14*mm)
    styles=getSampleStyleSheet()
    primary=_hex(cfg.ride_primary_hex)
    title=ParagraphStyle("RideTitle",parent=styles["Heading1"],fontSize=15,leading=18,textColor=primary,spaceAfter=4)
    small=ParagraphStyle("RideSmall",parent=styles["BodyText"],fontSize=8.5,leading=11)
    normal=ParagraphStyle("RideNormal",parent=styles["BodyText"],fontSize=9.5,leading=12)

    story=[]
    header=[]
    if cfg.ride_show_logo and cfg.ride_logo_path and Path(cfg.ride_logo_path).is_file():
        header.append(Image(cfg.ride_logo_path,width=45*mm,height=22*mm,kind="proportional"))
    else:
        header.append(Paragraph(cfg.sri_trade_name or cfg.sri_business_name or cfg.institution_name,title))

    header_text=[
        Paragraph(render_template(cfg.ride_title,values),title),
        Paragraph(render_template(cfg.ride_subtitle,values),small) if cfg.ride_subtitle else "",
    ]
    ht=Table([[header[0],header_text]],colWidths=[55*mm,125*mm])
    ht.setStyle(TableStyle([("VALIGN",(0,0),(-1,-1),"TOP"),("BOX",(0,0),(-1,-1),0.5,colors.lightgrey),("INNERGRID",(0,0),(-1,-1),0.25,colors.lightgrey),("PADDING",(0,0),(-1,-1),5)]))
    story += [ht,Spacer(1,5*mm)]

    issuer=[
        ["Razón social",cfg.sri_business_name or cfg.institution_name],
        ["RUC",cfg.sri_ruc or cfg.tax_id or ""],
        ["Dirección",cfg.address or ""],
        ["Factura",invoice.document_number or ""],
        ["Clave de acceso",invoice.access_key or ""],
        ["Autorización",invoice.authorization_number or ""],
        ["Fecha autorización",values["authorized_at"]],
        ["Ambiente","PRODUCCIÓN" if invoice.environment=="PRODUCTION" else "PRUEBAS"],
    ]
    t=Table(issuer,colWidths=[42*mm,138*mm])
    t.setStyle(TableStyle([("FONTNAME",(0,0),(0,-1),"Helvetica-Bold"),("FONTSIZE",(0,0),(-1,-1),8.5),("GRID",(0,0),(-1,-1),0.35,colors.lightgrey),("BACKGROUND",(0,0),(0,-1),colors.whitesmoke),("VALIGN",(0,0),(-1,-1),"TOP"),("PADDING",(0,0),(-1,-1),4)]))
    story += [t,Spacer(1,5*mm)]

    buyer=[
        ["Cliente",customer.full_name],
        ["Identificación",customer.identification],
        ["Dirección",customer.address or ""],
        ["Correo",customer.email or ""],
        ["Teléfono",customer.mobile or customer.phone or ""],
    ]
    b=Table(buyer,colWidths=[42*mm,138*mm])
    b.setStyle(TableStyle([("FONTNAME",(0,0),(0,-1),"Helvetica-Bold"),("FONTSIZE",(0,0),(-1,-1),8.5),("GRID",(0,0),(-1,-1),0.35,colors.lightgrey),("BACKGROUND",(0,0),(0,-1),colors.whitesmoke),("PADDING",(0,0),(-1,-1),4)]))
    story += [b,Spacer(1,5*mm)]

    detail=[
        ["Código","Descripción","Cant.","P. Unit.","Total"],
        [prop.code,f"Predio {prop.code}" + (f" - Clave catastral {prop.cadastral_key}" if prop.cadastral_key else ""),"1",f"{invoice.total:.2f}",f"{invoice.total:.2f}"],
    ]
    d=Table(detail,colWidths=[28*mm,85*mm,15*mm,25*mm,27*mm])
    d.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),primary),("TEXTCOLOR",(0,0),(-1,0),colors.white),("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),("FONTSIZE",(0,0),(-1,-1),8.5),("GRID",(0,0),(-1,-1),0.35,colors.lightgrey),("VALIGN",(0,0),(-1,-1),"TOP"),("ALIGN",(2,1),(-1,-1),"RIGHT"),("PADDING",(0,0),(-1,-1),4)]))
    story += [d,Spacer(1,4*mm)]

    totals=Table([["TOTAL",f"$ {invoice.total:.2f}"]],colWidths=[153*mm,27*mm])
    totals.setStyle(TableStyle([("FONTNAME",(0,0),(-1,-1),"Helvetica-Bold"),("ALIGN",(1,0),(1,0),"RIGHT"),("BOX",(0,0),(-1,-1),0.7,primary),("PADDING",(0,0),(-1,-1),5)]))
    story += [totals,Spacer(1,5*mm)]

    if cfg.ride_show_qr:
        qr_text=render_template(cfg.ride_qr_content_template,values)
        qr=qrcode.QRCode(border=1,box_size=4)
        qr.add_data(qr_text);qr.make(fit=True)
        image=qr.make_image(fill_color="black",back_color="white")
        buf=io.BytesIO();image.save(buf,format="PNG");buf.seek(0)
        size=int(cfg.ride_qr_size_mm or 28)*mm
        story += [Table([[Image(buf,width=size,height=size),Paragraph(f"<b>Clave de acceso</b><br/>{invoice.access_key}",small)]],colWidths=[size+4*mm,180*mm-size]),Spacer(1,3*mm)]

    if cfg.ride_additional_text:
        story += [Paragraph(render_template(cfg.ride_additional_text,values),normal),Spacer(1,3*mm)]
    story += [Paragraph(render_template(cfg.ride_footer,values),small)]

    doc.build(story)
    target.chmod(0o600)
    invoice.ride_path=str(target)
    return target
