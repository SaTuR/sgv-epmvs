from __future__ import annotations

import smtplib
import ssl
from datetime import datetime, timezone
from email.message import EmailMessage
from email.utils import formataddr
import httpx

from app.models import Customer, NotificationSetting, SystemSetting
from app.services.sri_signing import decrypt_secret

def normalize_ec_mobile(value:str|None)->str:
    raw="".join(ch for ch in (value or "") if ch.isdigit())
    if raw.startswith("593"): return "+"+raw
    if raw.startswith("0"): raw=raw[1:]
    if len(raw)==9 and raw.startswith("9"): return "+593"+raw
    if raw: return "+"+raw
    return ""

def send_whatsapp(cfg:NotificationSetting,customer:Customer,body:str)->str|None:
    if not cfg.whatsapp_enabled:
        raise ValueError("WhatsApp está desactivado.")
    if not cfg.whatsapp_phone_number_id or not cfg.whatsapp_access_token_encrypted:
        raise ValueError("La configuración de WhatsApp está incompleta.")
    to=normalize_ec_mobile(customer.mobile or customer.phone)
    if not to: raise ValueError("El cliente no tiene celular válido.")
    token=decrypt_secret(cfg.whatsapp_access_token_encrypted)
    url=f"https://graph.facebook.com/{cfg.whatsapp_api_version}/{cfg.whatsapp_phone_number_id}/messages"
    payload={"messaging_product":"whatsapp","recipient_type":"individual","to":to.lstrip("+"),"type":"text","text":{"preview_url":False,"body":body}}
    with httpx.Client(timeout=20) as client:
        r=client.post(url,headers={"Authorization":f"Bearer {token}","Content-Type":"application/json"},json=payload)
    if r.status_code>=300:
        raise ValueError(f"WhatsApp rechazó el mensaje ({r.status_code}): {r.text[:500]}")
    data=r.json()
    return ((data.get("messages") or [{}])[0]).get("id")

def send_sms(cfg:NotificationSetting,customer:Customer,body:str)->str|None:
    if not cfg.sms_enabled:
        raise ValueError("SMS está desactivado.")
    if cfg.sms_provider!="TWILIO":
        raise ValueError("Proveedor SMS no soportado.")
    if not cfg.sms_account_sid or not cfg.sms_auth_token_encrypted or not cfg.sms_from_number:
        raise ValueError("La configuración SMS está incompleta.")
    to=normalize_ec_mobile(customer.mobile or customer.phone)
    if not to: raise ValueError("El cliente no tiene celular válido.")
    token=decrypt_secret(cfg.sms_auth_token_encrypted)
    url=f"https://api.twilio.com/2010-04-01/Accounts/{cfg.sms_account_sid}/Messages.json"
    with httpx.Client(timeout=20) as client:
        r=client.post(url,auth=(cfg.sms_account_sid,token),data={"From":cfg.sms_from_number,"To":to,"Body":body})
    if r.status_code>=300:
        raise ValueError(f"Proveedor SMS rechazó el mensaje ({r.status_code}): {r.text[:500]}")
    return r.json().get("sid")

def send_email(cfg:NotificationSetting,system:SystemSetting,customer:Customer,subject:str|None,body:str)->str|None:
    if not cfg.email_enabled:
        raise ValueError("Email de notificaciones está desactivado.")
    if not customer.email:
        raise ValueError("El cliente no tiene correo electrónico.")
    if not system.smtp_host or not system.smtp_sender_email:
        raise ValueError("La configuración SMTP está incompleta.")
    msg=EmailMessage()
    msg["Subject"]=subject or "Notificación EPMVS"
    msg["From"]=formataddr((system.smtp_sender_name or system.institution_name,system.smtp_sender_email))
    msg["To"]=customer.email
    msg.set_content(body)
    password=decrypt_secret(system.smtp_password_encrypted) if system.smtp_password_encrypted else None
    if system.smtp_security=="SSL":
        with smtplib.SMTP_SSL(system.smtp_host,system.smtp_port,timeout=20,context=ssl.create_default_context()) as smtp:
            if system.smtp_username: smtp.login(system.smtp_username,password or "")
            smtp.send_message(msg)
    else:
        with smtplib.SMTP(system.smtp_host,system.smtp_port,timeout=20) as smtp:
            smtp.ehlo()
            if system.smtp_security=="STARTTLS":
                smtp.starttls(context=ssl.create_default_context());smtp.ehlo()
            if system.smtp_username: smtp.login(system.smtp_username,password or "")
            smtp.send_message(msg)
    return None
