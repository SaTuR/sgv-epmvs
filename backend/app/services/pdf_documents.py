from io import BytesIO
from pathlib import Path
from decimal import Decimal
import qrcode
from reportlab.lib import colors
from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

GREEN_DARK=HexColor("#3A6C32")
GREEN=HexColor("#52AD56")
YELLOW=HexColor("#FAB71C")
LIGHT=HexColor("#F5F8F4")
TEXT=HexColor("#1F2937")
MUTED=HexColor("#64748B")

LOGO_PATH=Path(__file__).resolve().parents[1]/"assets"/"epmvs-logo.webp"

styles=getSampleStyleSheet()
TITLE=ParagraphStyle("DocTitle",parent=styles["Heading1"],fontName="Helvetica-Bold",fontSize=15,leading=18,textColor=GREEN_DARK,spaceAfter=4)
SUB=ParagraphStyle("DocSub",parent=styles["Normal"],fontSize=8.5,leading=11,textColor=MUTED)
LABEL=ParagraphStyle("Label",parent=styles["Normal"],fontName="Helvetica-Bold",fontSize=8,textColor=MUTED)
VALUE=ParagraphStyle("Value",parent=styles["Normal"],fontSize=9.2,leading=12,textColor=TEXT)
SMALL=ParagraphStyle("Small",parent=styles["Normal"],fontSize=7.5,leading=9,textColor=MUTED)
RIGHT=ParagraphStyle("Right",parent=VALUE,alignment=TA_RIGHT)
CENTER=ParagraphStyle("Center",parent=VALUE,alignment=TA_CENTER)

def money(v):
    return f"$ {Decimal(v):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def qr_image(text:str):
    img=qrcode.make(text)
    buf=BytesIO(); img.save(buf,format="PNG"); buf.seek(0)
    return Image(buf,width=27*mm,height=27*mm)

def header_footer(canvas,doc,document_number:str,footer_text:str):
    canvas.saveState()
    w,h=A4
    canvas.setStrokeColor(GREEN)
    canvas.setLineWidth(2)
    canvas.line(18*mm,h-18*mm,w-18*mm,h-18*mm)
    canvas.setFont("Helvetica",7.5)
    canvas.setFillColor(MUTED)
    canvas.drawString(18*mm,12*mm,footer_text)
    canvas.drawRightString(w-18*mm,12*mm,f"{document_number} · Página {doc.page}")
    canvas.restoreState()

def institution_header(title,number,issued_at):
    logo=Image(str(LOGO_PATH),width=55*mm,height=21*mm)
    right=Table([
        [Paragraph(title,TITLE)],
        [Paragraph(f"<b>N.º:</b> {number}",VALUE)],
        [Paragraph(f"<b>Emitido:</b> {issued_at:%d/%m/%Y %H:%M}",VALUE)],
    ],colWidths=[86*mm])
    right.setStyle(TableStyle([("VALIGN",(0,0),(-1,-1),"TOP"),("ALIGN",(0,0),(-1,-1),"RIGHT")]))
    t=Table([[logo,right]],colWidths=[75*mm,86*mm])
    t.setStyle(TableStyle([("VALIGN",(0,0),(-1,-1),"MIDDLE"),("BOTTOMPADDING",(0,0),(-1,-1),7)]))
    return t

def section(title):
    t=Table([[Paragraph(title,ParagraphStyle("Sec",parent=VALUE,fontName="Helvetica-Bold",textColor=colors.white))]],colWidths=[169*mm])
    t.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,-1),GREEN_DARK),("LEFTPADDING",(0,0),(-1,-1),7),("TOPPADDING",(0,0),(-1,-1),5),("BOTTOMPADDING",(0,0),(-1,-1),5)]))
    return t

def info_table(rows):
    data=[]
    for left_label,left_value,right_label,right_value in rows:
        data.append([Paragraph(left_label,LABEL),Paragraph(str(left_value or "-"),VALUE),Paragraph(right_label,LABEL),Paragraph(str(right_value or "-"),VALUE)])
    t=Table(data,colWidths=[27*mm,57.5*mm,27*mm,57.5*mm])
    t.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,-1),colors.white),("GRID",(0,0),(-1,-1),0.35,HexColor("#DDE5DC")),
        ("VALIGN",(0,0),(-1,-1),"TOP"),("LEFTPADDING",(0,0),(-1,-1),5),("RIGHTPADDING",(0,0),(-1,-1),5),
        ("TOPPADDING",(0,0),(-1,-1),5),("BOTTOMPADDING",(0,0),(-1,-1),5),
    ]))
    return t

def final_block(story,verification_url,verification_code,user_name):
    story.append(Spacer(1,7*mm))
    qr=qr_image(verification_url)
    text=Paragraph(
        f"<b>Validación del documento</b><br/>Escanee el código QR o utilice el código:<br/>"
        f"<b>{verification_code}</b><br/><br/>Documento generado por: {user_name}",
        SMALL,
    )
    t=Table([[qr,text]],colWidths=[34*mm,135*mm])
    t.setStyle(TableStyle([("VALIGN",(0,0),(-1,-1),"MIDDLE"),("BOX",(0,0),(-1,-1),0.5,HexColor("#DDE5DC")),("BACKGROUND",(0,0),(-1,-1),LIGHT),("PADDING",(0,0),(-1,-1),7)]))
    story.append(t)
    story.append(Spacer(1,9*mm))
    sig=Table([
        ["",""],
        ["________________________________","________________________________"],
        [Paragraph("Responsable EPMVS",CENTER),Paragraph("Cliente / Beneficiario",CENTER)],
    ],colWidths=[75*mm,75*mm],hAlign="CENTER")
    sig.setStyle(TableStyle([("ALIGN",(0,0),(-1,-1),"CENTER"),("TOPPADDING",(0,0),(-1,-1),4)]))
    story.append(sig)

def build_pdf(story,number,footer_text="Sistema de Gestión y Venta EPMVS"):
    buf=BytesIO()
    doc=SimpleDocTemplate(buf,pagesize=A4,rightMargin=20*mm,leftMargin=20*mm,topMargin=24*mm,bottomMargin=20*mm)
    doc.build(story,onFirstPage=lambda c,d:header_footer(c,d,number,footer_text),onLaterPages=lambda c,d:header_footer(c,d,number,footer_text))
    buf.seek(0)
    return buf.getvalue()

def payment_receipt(ctx):
    d=ctx["document"]; p=ctx["payment"]; s=ctx["sale"]; c=ctx["customer"]; prop=ctx["property"]
    story=[institution_header("COMPROBANTE DE PAGO",d.document_number,d.created_at),Spacer(1,5*mm)]
    story += [section("DATOS DEL CLIENTE"),Spacer(1,2*mm),info_table([
        ("Identificación",c.identification,"Cliente",c.full_name),
        ("Teléfono",c.mobile or c.phone,"Correo",c.email),
    ]),Spacer(1,4*mm)]
    story += [section("DATOS DEL PREDIO"),Spacer(1,2*mm),info_table([
        ("Proyecto",ctx["project_name"],"Etapa",ctx["stage_name"]),
        ("Manzana",ctx["block_name"],"Lote",prop.lot_number),
        ("Código",prop.code,"Clave catastral",prop.cadastral_key),
    ]),Spacer(1,4*mm)]
    story += [section("DETALLE DEL PAGO"),Spacer(1,2*mm),info_table([
        ("Fecha de pago",p.payment_date.strftime("%d/%m/%Y"),"Forma de pago",p.payment_method),
        ("Referencia",p.reference,"Valor recibido",money(p.amount)),
        ("Saldo anterior",money(ctx["previous_balance"]),"Saldo actual",money(ctx["balance_after"])),
        ("Precio de venta",money(s.sale_price),"Entrada registrada",money(s.down_payment)),
    ])]
    if p.notes:
        story += [Spacer(1,3*mm),Paragraph(f"<b>Observaciones:</b> {p.notes}",VALUE)]
    final_block(story,ctx["verification_url"],d.verification_code,ctx["user_name"])
    return build_pdf(story,d.document_number,ctx.get("document_footer","Sistema de Gestión y Venta EPMVS"))

def account_statement(ctx):
    d=ctx["document"]; s=ctx["sale"]; c=ctx["customer"]; prop=ctx["property"]
    story=[institution_header("ESTADO DE CUENTA",d.document_number,d.created_at),Spacer(1,5*mm)]
    story += [section("DATOS GENERALES"),Spacer(1,2*mm),info_table([
        ("Cliente",c.full_name,"Identificación",c.identification),
        ("Proyecto",ctx["project_name"],"Etapa",ctx["stage_name"]),
        ("Manzana",ctx["block_name"],"Lote",prop.lot_number),
        ("Precio de venta",money(s.sale_price),"Entrada",money(s.down_payment)),
        ("Financiado",money(s.financed_amount),"Saldo pendiente",money(ctx["current_balance"])),
    ]),Spacer(1,4*mm),section("PLAN DE PAGOS"),Spacer(1,2*mm)]
    data=[[Paragraph("<b>#</b>",SMALL),Paragraph("<b>Vencimiento</b>",SMALL),Paragraph("<b>Cuota</b>",SMALL),Paragraph("<b>Pagado</b>",SMALL),Paragraph("<b>Saldo</b>",SMALL),Paragraph("<b>Estado</b>",SMALL)]]
    for i in ctx["installments"]:
        data.append([str(i.number),i.due_date.strftime("%d/%m/%Y"),money(i.amount),money(i.paid_amount),money(i.amount-i.paid_amount),ctx["status_label"](i)])
    t=Table(data,colWidths=[10*mm,31*mm,31*mm,31*mm,31*mm,35*mm],repeatRows=1)
    t.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),GREEN_DARK),("TEXTCOLOR",(0,0),(-1,0),colors.white),("GRID",(0,0),(-1,-1),0.35,HexColor("#DDE5DC")),("ALIGN",(2,1),(4,-1),"RIGHT"),("FONTSIZE",(0,1),(-1,-1),8),("TOPPADDING",(0,0),(-1,-1),5),("BOTTOMPADDING",(0,0),(-1,-1),5)]))
    story.append(t)
    final_block(story,ctx["verification_url"],d.verification_code,ctx["user_name"])
    return build_pdf(story,d.document_number)

def payments_certificate(ctx):
    d=ctx["document"]; s=ctx["sale"]; c=ctx["customer"]; prop=ctx["property"]
    story=[institution_header("CERTIFICADO DE PAGOS",d.document_number,d.created_at),Spacer(1,5*mm)]
    story.append(Paragraph(
        f"Por medio del presente documento se certifica que <b>{c.full_name}</b>, identificado/a con "
        f"<b>{c.identification}</b>, mantiene registrada la siguiente información de pagos respecto del predio indicado.",
        VALUE,
    ))
    story += [Spacer(1,5*mm),section("RESUMEN"),Spacer(1,2*mm),info_table([
        ("Proyecto",ctx["project_name"],"Etapa",ctx["stage_name"]),
        ("Manzana",ctx["block_name"],"Lote",prop.lot_number),
        ("Precio de venta",money(s.sale_price),"Total pagado",money(ctx["total_paid"])),
        ("Entrada",money(s.down_payment),"Saldo pendiente",money(ctx["current_balance"])),
    ]),Spacer(1,4*mm),section("PAGOS REGISTRADOS"),Spacer(1,2*mm)]
    data=[[Paragraph("<b>Fecha</b>",SMALL),Paragraph("<b>Forma</b>",SMALL),Paragraph("<b>Referencia</b>",SMALL),Paragraph("<b>Valor</b>",SMALL)]]
    for p in ctx["payments"]:
        data.append([p.payment_date.strftime("%d/%m/%Y"),p.payment_method,p.reference or "-",money(p.amount)])
    if len(data)==1:
        data.append(["-","-","No existen pagos registrados",money(0)])
    t=Table(data,colWidths=[35*mm,43*mm,58*mm,33*mm],repeatRows=1)
    t.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),GREEN_DARK),("TEXTCOLOR",(0,0),(-1,0),colors.white),("GRID",(0,0),(-1,-1),0.35,HexColor("#DDE5DC")),("ALIGN",(3,1),(3,-1),"RIGHT"),("FONTSIZE",(0,1),(-1,-1),8),("TOPPADDING",(0,0),(-1,-1),5),("BOTTOMPADDING",(0,0),(-1,-1),5)]))
    story.append(t)
    final_block(story,ctx["verification_url"],d.verification_code,ctx["user_name"])
    return build_pdf(story,d.document_number)
