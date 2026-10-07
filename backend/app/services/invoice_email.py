from __future__ import annotations

import smtplib
import ssl
import time
from email.message import EmailMessage
from email.utils import formataddr
from pathlib import Path

from app.models import Customer, ElectronicInvoice, Property, SystemSetting
from app.services.ride import render_template, template_values
from app.services.sri_signing import decrypt_secret


def _addresses(value:str|None)->list[str]:
    if not value:
        return []
    return [x.strip() for x in value.replace(";",",").split(",") if x.strip()]


def send_invoice_email(invoice:ElectronicInvoice,cfg:SystemSetting,customer:Customer,prop:Property)->None:
    if not cfg.invoice_email_enabled:
        raise ValueError("El envío de facturas por correo está desactivado.")
    if not customer.email:
        raise ValueError("El cliente no tiene correo electrónico configurado.")
    if not cfg.smtp_host or not cfg.smtp_sender_email:
        raise ValueError("La configuración SMTP está incompleta.")

    values=template_values(invoice,customer,prop)
    msg=EmailMessage()
    msg["Subject"]=render_template(cfg.invoice_email_subject_template,values)
    msg["From"]=formataddr((cfg.smtp_sender_name or cfg.sri_trade_name or cfg.institution_name,cfg.smtp_sender_email))
    msg["To"]=customer.email
    cc=_addresses(cfg.invoice_email_cc); bcc=_addresses(cfg.invoice_email_bcc)
    if cc: msg["Cc"]=", ".join(cc)
    msg.set_content(render_template(cfg.invoice_email_body_template,values))

    if cfg.invoice_email_attach_ride and invoice.ride_path and Path(invoice.ride_path).is_file():
        data=Path(invoice.ride_path).read_bytes()
        msg.add_attachment(data,maintype="application",subtype="pdf",filename=f"RIDE_{invoice.document_number}.pdf")
    if cfg.invoice_email_attach_xml and invoice.authorization_xml_path and Path(invoice.authorization_xml_path).is_file():
        data=Path(invoice.authorization_xml_path).read_bytes()
        msg.add_attachment(data,maintype="application",subtype="xml",filename=f"{invoice.access_key}_autorizado.xml")

    password=decrypt_secret(cfg.smtp_password_encrypted) if cfg.smtp_password_encrypted else None
    recipients=[customer.email,*cc,*bcc]
    attempts=max(1,int(cfg.invoice_email_retries or 0)+1)
    timeout=int(cfg.invoice_email_timeout_seconds or 20)
    last=None
    for attempt in range(attempts):
        try:
            if cfg.smtp_security=="SSL":
                with smtplib.SMTP_SSL(cfg.smtp_host,cfg.smtp_port,timeout=timeout,context=ssl.create_default_context()) as smtp:
                    if cfg.smtp_username: smtp.login(cfg.smtp_username,password or "")
                    smtp.send_message(msg,to_addrs=recipients)
            else:
                with smtplib.SMTP(cfg.smtp_host,cfg.smtp_port,timeout=timeout) as smtp:
                    smtp.ehlo()
                    if cfg.smtp_security=="STARTTLS":
                        smtp.starttls(context=ssl.create_default_context());smtp.ehlo()
                    if cfg.smtp_username: smtp.login(cfg.smtp_username,password or "")
                    smtp.send_message(msg,to_addrs=recipients)
            return
        except (OSError,smtplib.SMTPException) as exc:
            last=exc
            if attempt<attempts-1:
                time.sleep(min(2**attempt,5))
    raise ValueError(f"No fue posible enviar el correo: {last}")
