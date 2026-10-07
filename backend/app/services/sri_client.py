from __future__ import annotations

import base64
from datetime import datetime
from pathlib import Path
from typing import Any

import httpx
from lxml import etree

from app.models import ElectronicInvoice


TEST_RECEIPT_URL="https://celcer.sri.gob.ec/comprobantes-electronicos-ws/RecepcionComprobantesOffline"
TEST_AUTH_URL="https://celcer.sri.gob.ec/comprobantes-electronicos-ws/AutorizacionComprobantesOffline"
PROD_RECEIPT_URL="https://cel.sri.gob.ec/comprobantes-electronicos-ws/RecepcionComprobantesOffline"
PROD_AUTH_URL="https://cel.sri.gob.ec/comprobantes-electronicos-ws/AutorizacionComprobantesOffline"

SOAP_NS="http://schemas.xmlsoap.org/soap/envelope/"
REC_NS="http://ec.gob.sri.ws.recepcion"
AUTH_NS="http://ec.gob.sri.ws.autorizacion"


def endpoints(environment:str)->tuple[str,str]:
    if environment=="PRODUCTION":
        return PROD_RECEIPT_URL,PROD_AUTH_URL
    return TEST_RECEIPT_URL,TEST_AUTH_URL


def _soap_post(url:str,action:str,envelope:bytes,timeout:float=30.0)->bytes:
    headers={
        "Content-Type":"text/xml; charset=utf-8",
        "SOAPAction":action,
        "User-Agent":"SGV-EPMVS/1.0",
    }
    try:
        with httpx.Client(timeout=timeout,verify=True,follow_redirects=True) as client:
            response=client.post(url,content=envelope,headers=headers)
            response.raise_for_status()
            return response.content
    except httpx.TimeoutException as exc:
        raise ValueError("Tiempo de espera agotado al conectar con el SRI.") from exc
    except httpx.HTTPError as exc:
        raise ValueError(f"Error de comunicación con el SRI: {exc}") from exc


def _texts(node:etree._Element,xpath:str)->list[str]:
    return [str(x).strip() for x in node.xpath(xpath) if str(x).strip()]


def _messages(root:etree._Element)->list[str]:
    messages=[]
    nodes=root.xpath("//*[local-name()='mensaje']")
    for node in nodes:
        identifier=_texts(node,"./*[local-name()='identificador']/text()")
        message=_texts(node,"./*[local-name()='mensaje']/text()")
        additional=_texts(node,"./*[local-name()='informacionAdicional']/text()")
        msg=" - ".join(
            [x for x in [
                identifier[0] if identifier else "",
                message[0] if message else "",
                additional[0] if additional else "",
            ] if x]
        )
        if msg and msg not in messages:
            messages.append(msg)
    return messages


def build_receipt_envelope(xml_bytes:bytes)->bytes:
    encoded=base64.b64encode(xml_bytes).decode("ascii")
    root=etree.Element(etree.QName(SOAP_NS,"Envelope"),nsmap={"soapenv":SOAP_NS,"ec":REC_NS})
    body=etree.SubElement(root,etree.QName(SOAP_NS,"Body"))
    operation=etree.SubElement(body,etree.QName(REC_NS,"validarComprobante"))
    xml=etree.SubElement(operation,"xml")
    xml.text=encoded
    return etree.tostring(root,encoding="UTF-8",xml_declaration=True)


def build_authorization_envelope(access_key:str)->bytes:
    root=etree.Element(etree.QName(SOAP_NS,"Envelope"),nsmap={"soapenv":SOAP_NS,"ec":AUTH_NS})
    body=etree.SubElement(root,etree.QName(SOAP_NS,"Body"))
    operation=etree.SubElement(body,etree.QName(AUTH_NS,"autorizacionComprobante"))
    key=etree.SubElement(operation,"claveAccesoComprobante")
    key.text=access_key
    return etree.tostring(root,encoding="UTF-8",xml_declaration=True)


def parse_receipt_response(xml_bytes:bytes)->dict[str,Any]:
    try:
        root=etree.fromstring(xml_bytes)
    except etree.XMLSyntaxError as exc:
        raise ValueError("El SRI devolvió una respuesta de recepción inválida.") from exc
    states=_texts(root,"//*[local-name()='estado']/text()")
    state=states[0].upper() if states else ""
    if state not in {"RECIBIDA","DEVUELTA"}:
        raise ValueError("El SRI no devolvió un estado de recepción reconocido.")
    return {"state":state,"messages":_messages(root),"raw":xml_bytes.decode("utf-8","replace")}


def parse_authorization_response(xml_bytes:bytes)->dict[str,Any]:
    try:
        root=etree.fromstring(xml_bytes)
    except etree.XMLSyntaxError as exc:
        raise ValueError("El SRI devolvió una respuesta de autorización inválida.") from exc

    authorization_nodes=root.xpath("//*[local-name()='autorizacion']")
    if not authorization_nodes:
        return {
            "state":"PENDING",
            "authorization_number":None,
            "authorization_date":None,
            "environment":None,
            "document_xml":None,
            "messages":_messages(root),
            "raw":xml_bytes.decode("utf-8","replace"),
        }

    auth=authorization_nodes[0]
    states=_texts(auth,"./*[local-name()='estado']/text()")
    numbers=_texts(auth,"./*[local-name()='numeroAutorizacion']/text()")
    dates=_texts(auth,"./*[local-name()='fechaAutorizacion']/text()")
    environments=_texts(auth,"./*[local-name()='ambiente']/text()")
    documents=_texts(auth,"./*[local-name()='comprobante']/text()")
    state=states[0].upper() if states else "PENDING"
    authorization_date=None
    if dates:
        try:
            authorization_date=datetime.fromisoformat(dates[0].replace("Z","+00:00"))
        except ValueError:
            authorization_date=None
    return {
        "state":state,
        "authorization_number":numbers[0] if numbers else None,
        "authorization_date":authorization_date,
        "environment":environments[0] if environments else None,
        "document_xml":documents[0] if documents else None,
        "messages":_messages(auth),
        "raw":xml_bytes.decode("utf-8","replace"),
    }


def send_receipt(invoice:ElectronicInvoice)->dict[str,Any]:
    if invoice.status!="SIGNED":
        raise ValueError("Solo se puede enviar al SRI una factura firmada.")
    if not invoice.signed_xml_path or not Path(invoice.signed_xml_path).is_file():
        raise ValueError("No se encontró el XML firmado.")
    receipt_url,_=endpoints(invoice.environment)
    envelope=build_receipt_envelope(Path(invoice.signed_xml_path).read_bytes())
    response=_soap_post(receipt_url,"validarComprobante",envelope)
    return parse_receipt_response(response)


def request_authorization(invoice:ElectronicInvoice)->dict[str,Any]:
    if invoice.status!="SENT":
        raise ValueError("La factura debe haber sido recibida por el SRI antes de consultar autorización.")
    if not invoice.access_key:
        raise ValueError("La factura no tiene clave de acceso.")
    _,auth_url=endpoints(invoice.environment)
    envelope=build_authorization_envelope(invoice.access_key)
    response=_soap_post(auth_url,"autorizacionComprobante",envelope)
    return parse_authorization_response(response)


def save_authorization_xml(invoice:ElectronicInvoice,result:dict[str,Any])->Path|None:
    document_xml=result.get("document_xml")
    if not document_xml or not invoice.signed_xml_path:
        return None
    target=Path(invoice.signed_xml_path).with_name(f"{invoice.access_key}_authorized.xml")
    authorization=etree.Element("autorizacion")
    etree.SubElement(authorization,"estado").text=result.get("state") or ""
    etree.SubElement(authorization,"numeroAutorizacion").text=result.get("authorization_number") or ""
    if result.get("authorization_date"):
        etree.SubElement(authorization,"fechaAutorizacion").text=result["authorization_date"].isoformat()
    etree.SubElement(authorization,"ambiente").text=result.get("environment") or ""
    comprobante=etree.SubElement(authorization,"comprobante")
    comprobante.text=etree.CDATA(document_xml)
    target.write_bytes(etree.tostring(authorization,encoding="UTF-8",xml_declaration=True,pretty_print=True))
    target.chmod(0o600)
    return target
