from __future__ import annotations

import io
from decimal import Decimal
from pathlib import Path

import qrcode
from reportlab.graphics.barcode import createBarcodeDrawing
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, LETTER
from reportlab.lib.units import mm
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

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
        "authorized_at":invoice.authorized_at.strftime("%Y-%m-%d %H:%M:%S%z") if invoice.authorized_at else "",
    }


def render_template(text:str|None,values:dict[str,str])->str:
    result=text or ""
    for key,value in values.items():
        result=result.replace("{"+key+"}",value)
    return result


def _hex(value:str,default="#000000"):
    try:
        return colors.HexColor(value)
    except Exception:
        return colors.HexColor(default)


def _money(value:Decimal|float|int)->str:
    return f"{Decimal(value):.2f}"


def _tax_values(invoice:ElectronicInvoice,cfg:SystemSetting)->dict[str,Decimal]:
    gross=Decimal(invoice.total)
    rate=Decimal(str(cfg.sri_tax_rate or 0))
    if rate>0 and cfg.sri_prices_include_tax:
        base=(gross/(Decimal("1")+(rate/Decimal("100")))).quantize(Decimal("0.01"))
        tax=(gross-base).quantize(Decimal("0.01"))
        total=gross.quantize(Decimal("0.01"))
    elif rate>0:
        base=gross.quantize(Decimal("0.01"))
        tax=(base*rate/Decimal("100")).quantize(Decimal("0.01"))
        total=(base+tax).quantize(Decimal("0.01"))
    else:
        base=gross.quantize(Decimal("0.01"))
        tax=Decimal("0.00")
        total=gross.quantize(Decimal("0.01"))

    pct=(cfg.sri_tax_percentage_code or "").strip()
    subtotal_taxed=base if rate>0 else Decimal("0.00")
    subtotal_zero=base if rate==0 and pct not in {"6","7"} else Decimal("0.00")
    subtotal_not_subject=base if rate==0 and pct=="6" else Decimal("0.00")
    subtotal_exempt=base if rate==0 and pct=="7" else Decimal("0.00")
    return {
        "base":base,
        "tax":tax,
        "total":total,
        "subtotal_taxed":subtotal_taxed,
        "subtotal_zero":subtotal_zero,
        "subtotal_not_subject":subtotal_not_subject,
        "subtotal_exempt":subtotal_exempt,
        "rate":rate,
    }


def _payment_method_label(code:str|None)->str:
    labels={
        "01":"SIN UTILIZACIÓN DEL SISTEMA FINANCIERO",
        "15":"COMPENSACIÓN DE DEUDAS",
        "16":"TARJETA DE DÉBITO",
        "17":"DINERO ELECTRÓNICO",
        "18":"TARJETA PREPAGO",
        "19":"TARJETA DE CRÉDITO",
        "20":"OTROS CON UTILIZACIÓN DEL SISTEMA FINANCIERO",
        "21":"ENDOSO DE TÍTULOS",
    }
    return labels.get((code or "").strip(),code or "")


def _access_code_flowable(invoice:ElectronicInvoice,cfg:SystemSetting):
    key=invoice.access_key or ""
    code_type=(cfg.ride_code_type or "BARCODE").upper()
    if code_type=="NONE":
        return Paragraph(key,ParagraphStyle("AccessPlain",fontName="Helvetica",fontSize=7.3,leading=9))
    if code_type=="QR":
        qr=qrcode.QRCode(border=1,box_size=4)
        qr.add_data(render_template(cfg.ride_qr_content_template or "{access_key}",{"access_key":key}))
        qr.make(fit=True)
        image=qr.make_image(fill_color="black",back_color="white")
        buf=io.BytesIO();image.save(buf,format="PNG");buf.seek(0)
        size=int(cfg.ride_qr_size_mm or 28)*mm
        return Image(buf,width=size,height=size)
    return createBarcodeDrawing(
        "Code128",
        value=key,
        barHeight=int(cfg.ride_barcode_height_mm or 18)*mm,
        humanReadable=True,
        fontName="Helvetica",
        fontSize=6.5,
        quiet=False,
    )


def generate_ride(invoice:ElectronicInvoice,cfg:SystemSetting,customer:Customer,prop:Property,sale:Sale)->Path:
    if invoice.status!="AUTHORIZED":
        raise ValueError("El RIDE solo puede generarse para una factura autorizada por el SRI.")

    values=template_values(invoice,customer,prop)
    tax=_tax_values(invoice,cfg)
    root=Path(app_settings.upload_path)/"electronic_invoices"/str(invoice.issue_date.year)
    root.mkdir(parents=True,exist_ok=True)
    target=root/f"{invoice.access_key}_RIDE.pdf"

    pagesize=A4 if cfg.ride_page_size=="A4" else LETTER
    page_width,page_height=pagesize
    usable_width=page_width-20*mm
    doc=SimpleDocTemplate(
        str(target),pagesize=pagesize,
        rightMargin=10*mm,leftMargin=10*mm,topMargin=9*mm,bottomMargin=10*mm,
    )

    styles=getSampleStyleSheet()
    black=colors.black
    title=ParagraphStyle("RideTitle",parent=styles["Heading1"],fontName="Helvetica-Bold",fontSize=14.5,leading=17,textColor=black,spaceAfter=3)
    bold=ParagraphStyle("RideBold",parent=styles["BodyText"],fontName="Helvetica-Bold",fontSize=8.5,leading=10.5)
    normal=ParagraphStyle("RideNormal",parent=styles["BodyText"],fontName="Helvetica",fontSize=8.2,leading=10.3)
    small=ParagraphStyle("RideSmall",parent=styles["BodyText"],fontName="Helvetica",fontSize=7.2,leading=8.8)
    section=ParagraphStyle("RideSection",parent=bold,fontSize=10.5,leading=12.5)

    story=[]

    # Encabezado: emisor a la izquierda, datos fiscales a la derecha.
    left=[]
    if cfg.ride_show_logo and cfg.ride_logo_path and Path(cfg.ride_logo_path).is_file():
        left.append(Image(cfg.ride_logo_path,width=48*mm,height=23*mm,kind="proportional"))
        left.append(Spacer(1,2*mm))
    left += [
        Paragraph(cfg.sri_trade_name or cfg.sri_business_name or cfg.institution_name,bold),
        Paragraph(f"<b>Dir. Matriz:</b> {cfg.address or ''}",normal),
        Paragraph(f"<b>Obligado a llevar contabilidad:</b> {'SI' if cfg.sri_accounting_required else 'NO'}",normal),
    ]
    if cfg.sri_special_taxpayer_code:
        left.append(Paragraph(f"<b>Contribuyente Especial:</b> {cfg.sri_special_taxpayer_code}",normal))
    if cfg.sri_withholding_agent_code:
        left.append(Paragraph(f"<b>Agente de Retención:</b> {cfg.sri_withholding_agent_code}",normal))

    right=[
        Paragraph(f"<b>RUC:</b> {cfg.sri_ruc or cfg.tax_id or ''}",bold),
        Spacer(1,1.5*mm),
        Paragraph("<b>AUTORIZADO</b>",normal),
        Paragraph(render_template(cfg.ride_title or "Factura Electrónica",values),title),
        Paragraph(f"<b>No.</b> {invoice.document_number or ''}",bold),
        Spacer(1,1.5*mm),
        Paragraph("<b>Número de Autorización:</b>",bold),
        Paragraph(invoice.authorization_number or "",small),
        Spacer(1,1*mm),
        Paragraph(f"<b>Fecha y Hora de Autorización:</b> {values['authorized_at']}",normal),
        Paragraph(f"<b>Ambiente:</b> {'Producción' if invoice.environment=='PRODUCTION' else 'Pruebas'}",normal),
        Paragraph("<b>Emisión:</b> Normal",normal),
        Spacer(1,1*mm),
        Paragraph("<b>Clave de Acceso:</b>",bold),
        _access_code_flowable(invoice,cfg),
    ]
    if cfg.ride_subtitle:
        right.insert(4,Paragraph(render_template(cfg.ride_subtitle,values),small))

    top=Table([[left,right]],colWidths=[usable_width*0.53,usable_width*0.47])
    top.setStyle(TableStyle([
        ("VALIGN",(0,0),(-1,-1),"BOTTOM"),
        ("LEFTPADDING",(0,0),(-1,-1),5),
        ("RIGHTPADDING",(0,0),(-1,-1),5),
        ("TOPPADDING",(0,0),(-1,-1),4),
        ("BOTTOMPADDING",(0,0),(-1,-1),4),
    ]))
    story += [top,Spacer(1,4*mm)]

    # Información del comprador.
    buyer_rows=[
        [Paragraph("<b>Información del Comprador</b>",section),""],
        [Paragraph("<b>Nombre:</b>",normal),Paragraph(customer.full_name,normal)],
        [Paragraph(f"<b>{'RUC' if customer.identification_type=='RUC' else 'CI'}:</b>",normal),Paragraph(customer.identification,normal)],
        [Paragraph("<b>Fecha emisión:</b>",normal),Paragraph(invoice.issue_date.strftime("%d/%m/%Y"),normal)],
    ]
    if customer.address:
        buyer_rows.append([Paragraph("<b>Dirección:</b>",normal),Paragraph(customer.address,normal)])
    buyer=Table(buyer_rows,colWidths=[35*mm,usable_width-35*mm])
    buyer.setStyle(TableStyle([
        ("SPAN",(0,0),(1,0)),
        ("BOX",(0,0),(-1,-1),0.8,black),
        ("VALIGN",(0,0),(-1,-1),"TOP"),
        ("LEFTPADDING",(0,0),(-1,-1),4),
        ("RIGHTPADDING",(0,0),(-1,-1),4),
        ("TOPPADDING",(0,0),(-1,-1),2.5),
        ("BOTTOMPADDING",(0,0),(-1,-1),2.5),
    ]))
    story += [buyer,Spacer(1,4*mm)]

    # Detalle, con la misma estructura visual del RIDE de referencia.
    description=f"Predio {prop.code}"
    if prop.location_reference:
        description+=f" - {prop.location_reference}"
    detail=[
        [Paragraph("<b>Cód.<br/>Principal</b>",small),Paragraph("<b>Cód.<br/>Auxiliar</b>",small),Paragraph("<b>Descripción</b>",small),
         Paragraph("<b>Cant.</b>",small),Paragraph("<b>Precio<br/>Unit.</b>",small),Paragraph("<b>Desc.</b>",small),Paragraph("<b>Precio<br/>Total</b>",small)],
        [Paragraph(prop.code,small),Paragraph(prop.cadastral_key or "",small),Paragraph(description,small),
         Paragraph("1",small),Paragraph(_money(tax["base"]),small),Paragraph("0.00",small),Paragraph(_money(tax["base"]),small)],
    ]
    widths=[22*mm,22*mm,60*mm,14*mm,22*mm,18*mm,22*mm]
    detail_table=Table(detail,colWidths=widths)
    detail_table.setStyle(TableStyle([
        ("GRID",(0,0),(-1,-1),0.75,black),
        ("BACKGROUND",(0,0),(-1,0),colors.HexColor("#F2F2F2")),
        ("ALIGN",(0,0),(-1,0),"CENTER"),
        ("ALIGN",(3,1),(-1,-1),"RIGHT"),
        ("VALIGN",(0,0),(-1,-1),"MIDDLE"),
        ("LEFTPADDING",(0,0),(-1,-1),3),
        ("RIGHTPADDING",(0,0),(-1,-1),3),
        ("TOPPADDING",(0,0),(-1,-1),4),
        ("BOTTOMPADDING",(0,0),(-1,-1),4),
    ]))
    story += [detail_table,Spacer(1,4*mm)]

    # Información adicional y totales.
    additional_rows=[[Paragraph("<b>Información Adicional</b>",section)]]
    if cfg.sri_software_provider_ruc:
        additional_rows.append([Paragraph(f"<b>RUC Proveedor:</b> {cfg.sri_software_provider_ruc}",normal)])
    additional_rows.append([Paragraph(f"<b>Predio:</b> {prop.code}",normal)])
    if prop.cadastral_key:
        additional_rows.append([Paragraph(f"<b>Clave catastral:</b> {prop.cadastral_key}",normal)])
    if cfg.ride_additional_text:
        additional_rows.append([Paragraph(render_template(cfg.ride_additional_text,values),normal)])
    additional=Table(additional_rows,colWidths=[usable_width*0.50-3*mm])
    additional.setStyle(TableStyle([
        ("BOX",(0,0),(-1,-1),0.75,black),
        ("VALIGN",(0,0),(-1,-1),"TOP"),
        ("LEFTPADDING",(0,0),(-1,-1),4),
        ("RIGHTPADDING",(0,0),(-1,-1),4),
        ("TOPPADDING",(0,0),(-1,-1),4),
        ("BOTTOMPADDING",(0,0),(-1,-1),4),
    ]))

    rate_label=f"{tax['rate'].normalize()}%" if tax["rate"]>0 else "0%"
    totals_rows=[
        [f"SUBTOTAL {rate_label}",_money(tax["subtotal_taxed"])],
        ["SUBTOTAL 0%",_money(tax["subtotal_zero"])],
        ["SUBTOTAL NO OBJETO IVA",_money(tax["subtotal_not_subject"])],
        ["SUBTOTAL EXENTO IVA",_money(tax["subtotal_exempt"])],
        ["SUBTOTAL SIN IMPUESTOS",_money(tax["base"])],
        ["ICE","0.00"],
        [f"IVA {rate_label}",_money(tax["tax"])],
        ["PROPINA","0.00"],
        ["VALOR TOTAL",_money(tax["total"])],
    ]
    totals=Table(totals_rows,colWidths=[usable_width*0.36,usable_width*0.14-3*mm])
    totals.setStyle(TableStyle([
        ("GRID",(0,0),(-1,-1),0.7,black),
        ("FONTNAME",(0,-1),(-1,-1),"Helvetica-Bold"),
        ("FONTSIZE",(0,0),(-1,-1),7.6),
        ("ALIGN",(1,0),(1,-1),"RIGHT"),
        ("BACKGROUND",(0,-1),(-1,-1),colors.HexColor("#F2F2F2")),
        ("LEFTPADDING",(0,0),(-1,-1),4),
        ("RIGHTPADDING",(0,0),(-1,-1),4),
        ("TOPPADDING",(0,0),(-1,-1),3),
        ("BOTTOMPADDING",(0,0),(-1,-1),3),
    ]))

    left_bottom=[]
    if cfg.ride_show_additional_info:
        left_bottom += [additional,Spacer(1,3*mm)]
    if cfg.ride_show_payment_table:
        payment=[
            [Paragraph("<b>Forma de Pago</b>",small),Paragraph("<b>Valor</b>",small),Paragraph("<b>Plazo</b>",small),Paragraph("<b>Tiempo</b>",small)],
            [Paragraph(_payment_method_label(cfg.sri_payment_method_code),small),Paragraph(_money(tax["total"]),small),Paragraph("0",small),Paragraph("días",small)],
        ]
        pay=Table(payment,colWidths=[usable_width*0.29,usable_width*0.08,usable_width*0.06,usable_width*0.07-3*mm])
        pay.setStyle(TableStyle([
            ("GRID",(0,0),(-1,-1),0.7,black),
            ("BACKGROUND",(0,0),(-1,0),colors.HexColor("#F2F2F2")),
            ("ALIGN",(1,1),(2,1),"RIGHT"),
            ("VALIGN",(0,0),(-1,-1),"MIDDLE"),
            ("LEFTPADDING",(0,0),(-1,-1),3),
            ("RIGHTPADDING",(0,0),(-1,-1),3),
            ("TOPPADDING",(0,0),(-1,-1),4),
            ("BOTTOMPADDING",(0,0),(-1,-1),4),
        ]))
        left_bottom.append(pay)

    bottom=Table([[left_bottom,totals]],colWidths=[usable_width*0.52,usable_width*0.48])
    bottom.setStyle(TableStyle([
        ("VALIGN",(0,0),(-1,-1),"TOP"),
        ("LEFTPADDING",(0,0),(-1,-1),0),
        ("RIGHTPADDING",(0,0),(-1,-1),0),
        ("TOPPADDING",(0,0),(-1,-1),0),
        ("BOTTOMPADDING",(0,0),(-1,-1),0),
    ]))
    story += [bottom,Spacer(1,5*mm)]

    footer=render_template(cfg.ride_footer or "Documento generado electrónicamente",values)
    story.append(Paragraph(footer,ParagraphStyle("RideFooter",parent=small,alignment=1,textColor=colors.HexColor("#666666"))))

    doc.build(story)
    target.chmod(0o600)
    invoice.ride_path=str(target)
    return target
