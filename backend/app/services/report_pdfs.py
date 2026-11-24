from io import BytesIO
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

GREEN_DARK=HexColor("#3A6C32")
GREEN=HexColor("#52AD56")
TEXT=HexColor("#1F2937")
MUTED=HexColor("#64748B")
LOGO_PATH=Path(__file__).resolve().parents[1]/"assets"/"epmvs-logo.webp"
styles=getSampleStyleSheet()
TITLE=ParagraphStyle("title",parent=styles["Heading1"],fontName="Helvetica-Bold",fontSize=18,leading=21,textColor=GREEN_DARK,spaceAfter=3)
SMALL=ParagraphStyle("small",parent=styles["Normal"],fontSize=8.5,leading=11,textColor=TEXT)
HEADER_SMALL=ParagraphStyle("header-small",parent=styles["Normal"],fontSize=8.5,leading=11,textColor=TEXT)

def money(v):
    return f"$ {Decimal(str(v or 0)):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def report_header(filters_text):
    logo=Image(str(LOGO_PATH),width=48*mm,height=18.5*mm)
    right=Table([
        [Paragraph("REPORTE DE COMISIONES",TITLE)],
    ],colWidths=[198*mm])
    right.setStyle(TableStyle([
        ("VALIGN",(0,0),(-1,-1),"TOP"),
        ("LEFTPADDING",(0,0),(-1,-1),0),
        ("RIGHTPADDING",(0,0),(-1,-1),0),
        ("TOPPADDING",(0,0),(-1,-1),0),
        ("BOTTOMPADDING",(0,0),(-1,-1),0),
    ]))
    header=Table([[logo,right]],colWidths=[55*mm,198*mm])
    header.setStyle(TableStyle([
        ("VALIGN",(0,0),(-1,-1),"MIDDLE"),
        ("LEFTPADDING",(0,0),(-1,-1),0),
        ("RIGHTPADDING",(0,0),(-1,-1),4),
        ("TOPPADDING",(0,0),(-1,-1),0),
        ("BOTTOMPADDING",(0,0),(-1,-1),5),
        ("LINEAFTER",(0,0),(0,0),1.2,GREEN_DARK),
    ]))
    return header

def commissions_pdf(summary,detail,filters_text):
    buf=BytesIO()
    doc=SimpleDocTemplate(buf,pagesize=landscape(A4),rightMargin=12*mm,leftMargin=12*mm,topMargin=12*mm,bottomMargin=12*mm)
    story=[
        report_header(filters_text),
        Spacer(1,4*mm),
    ]
    totals=summary["totals"]
    kpi=[
        ["Valor vendido","Comisión generada","Pendiente","Aprobada","Pagada","Anulada"],
        [money(totals["sold_amount"]),money(totals["generated"]),money(totals["pending"]),money(totals["approved"]),money(totals["paid"]),money(totals["cancelled"])],
    ]
    t=Table(kpi,colWidths=[43*mm]*6)
    t.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,0),GREEN_DARK),("TEXTCOLOR",(0,0),(-1,0),colors.white),
        ("GRID",(0,0),(-1,-1),0.35,HexColor("#DDE5DC")),("ALIGN",(0,0),(-1,-1),"CENTER"),
        ("FONTSIZE",(0,0),(-1,-1),8),("TOPPADDING",(0,0),(-1,-1),5),("BOTTOMPADDING",(0,0),(-1,-1),5),
    ]))
    story += [t,Spacer(1,5*mm),Paragraph("Resumen por vendedor",styles["Heading2"]),Spacer(1,2*mm)]
    data=[["Vendedor","Ventas","Valor vendido","Generada","Pendiente","Aprobada","Pagada","Anulada"]]
    for r in summary["sellers"]:
        data.append([r["seller"],str(r["sales_count"]),money(r["sold_amount"]),money(r["generated"]),money(r["pending"]),money(r["approved"]),money(r["paid"]),money(r["cancelled"])])
    ts=Table(data,colWidths=[54*mm,18*mm,33*mm,30*mm,30*mm,30*mm,30*mm,30*mm],repeatRows=1)
    ts.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),GREEN_DARK),("TEXTCOLOR",(0,0),(-1,0),colors.white),("GRID",(0,0),(-1,-1),0.3,HexColor("#DDE5DC")),("FONTSIZE",(0,0),(-1,-1),7),("ALIGN",(1,1),(-1,-1),"RIGHT")]))
    story += [ts,Spacer(1,5*mm),Paragraph("Detalle",styles["Heading2"]),Spacer(1,2*mm)]
    dd=[["Fecha","Vendedor","Cliente","Etapa","Predio","Venta","%","Comisión","Estado"]]
    for r in detail:
        dd.append([str(r["date"]),r["seller"],r["customer"],r["stage"],r["property"],money(r["sale_price"]),f'{r["commission_rate"]:.2f}%',money(r["commission_amount"]),r["status_label"]])
    td=Table(dd,colWidths=[23*mm,43*mm,48*mm,24*mm,32*mm,28*mm,15*mm,28*mm,24*mm],repeatRows=1)
    td.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),GREEN_DARK),("TEXTCOLOR",(0,0),(-1,0),colors.white),("GRID",(0,0),(-1,-1),0.3,HexColor("#DDE5DC")),("FONTSIZE",(0,0),(-1,-1),6.5),("ALIGN",(5,1),(7,-1),"RIGHT")]))
    story.append(td)
    doc.build(story)
    buf.seek(0)
    return buf.getvalue()
