from __future__ import annotations

import base64
import hashlib
from datetime import datetime, timezone
from pathlib import Path

from cryptography import x509
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import pkcs12
from lxml import etree
from signxml import DigestAlgorithm, SignatureMethod
from signxml.xades import XAdESDataObjectFormat, XAdESSignatureConfiguration, XAdESSigner, XAdESVerifier

from app.config import settings as app_settings
from app.models import ElectronicInvoice, SystemSetting


CERT_DIR=Path(app_settings.upload_path)/"sri"
CERT_PATH=CERT_DIR/"firma_electronica.p12"


def _fernet()->Fernet:
    raw=hashlib.sha256(app_settings.secret_key.encode("utf-8")).digest()
    return Fernet(base64.urlsafe_b64encode(raw))


def encrypt_secret(value:str)->str:
    return _fernet().encrypt(value.encode("utf-8")).decode("ascii")


def decrypt_secret(value:str)->str:
    try:
        return _fernet().decrypt(value.encode("ascii")).decode("utf-8")
    except InvalidToken as exc:
        raise ValueError("No fue posible descifrar la contraseña del certificado. Verifique SECRET_KEY.") from exc


def _cert_times(cert:x509.Certificate):
    valid_from=getattr(cert,"not_valid_before_utc",None)
    valid_to=getattr(cert,"not_valid_after_utc",None)
    if valid_from is None:
        valid_from=cert.not_valid_before.replace(tzinfo=timezone.utc)
    if valid_to is None:
        valid_to=cert.not_valid_after.replace(tzinfo=timezone.utc)
    return valid_from,valid_to


def load_pkcs12(data:bytes,password:str):
    try:
        key,cert,chain=pkcs12.load_key_and_certificates(data,password.encode("utf-8"))
    except Exception as exc:
        raise ValueError("No se pudo abrir el certificado. Verifique el archivo y la contraseña.") from exc
    if key is None or cert is None:
        raise ValueError("El archivo no contiene una clave privada y certificado utilizables.")
    if not isinstance(key,rsa.RSAPrivateKey):
        raise ValueError("El SRI requiere un certificado con clave RSA.")
    if key.key_size!=2048:
        raise ValueError("El SRI requiere una clave RSA de 2048 bits.")
    valid_from,valid_to=_cert_times(cert)
    now=datetime.now(timezone.utc)
    if now<valid_from:
        raise ValueError("El certificado todavía no es válido.")
    if now>valid_to:
        raise ValueError("El certificado está vencido.")
    return key,cert,list(chain or []),valid_from,valid_to


def install_certificate(data:bytes,password:str,row:SystemSetting)->dict:
    key,cert,chain,valid_from,valid_to=load_pkcs12(data,password)
    CERT_DIR.mkdir(parents=True,exist_ok=True)
    CERT_PATH.write_bytes(data)
    CERT_PATH.chmod(0o600)

    row.sri_certificate_path=str(CERT_PATH)
    row.sri_certificate_password_encrypted=encrypt_secret(password)
    row.sri_certificate_subject=cert.subject.rfc4514_string()
    row.sri_certificate_issuer=cert.issuer.rfc4514_string()
    row.sri_certificate_serial=str(cert.serial_number)
    row.sri_certificate_valid_from=valid_from
    row.sri_certificate_valid_to=valid_to

    return {
        "subject":row.sri_certificate_subject,
        "issuer":row.sri_certificate_issuer,
        "serial":row.sri_certificate_serial,
        "valid_from":valid_from,
        "valid_to":valid_to,
        "chain_length":len(chain),
    }


def certificate_ready(row:SystemSetting)->bool:
    return bool(
        row.sri_certificate_path
        and row.sri_certificate_password_encrypted
        and Path(row.sri_certificate_path).is_file()
    )


def _load_installed_certificate(row:SystemSetting):
    if not certificate_ready(row):
        raise ValueError("No existe un certificado electrónico configurado.")
    password=decrypt_secret(row.sri_certificate_password_encrypted)
    data=Path(row.sri_certificate_path).read_bytes()
    return load_pkcs12(data,password)


class SriXAdESSigner(XAdESSigner):
    def check_deprecated_methods(self):
        # El SRI exige RSA-SHA1 en su ficha técnica vigente.
        return


def sign_invoice_xml(invoice:ElectronicInvoice,row:SystemSetting)->Path:
    if not invoice.xml_path or not Path(invoice.xml_path).is_file():
        raise ValueError("Primero debe generar el XML de la factura.")
    if invoice.status!="XML_GENERATED":
        raise ValueError("La factura no está en estado XML generado.")

    key,cert,chain,valid_from,valid_to=_load_installed_certificate(row)
    now=datetime.now(timezone.utc)
    if now<valid_from or now>valid_to:
        raise ValueError("El certificado electrónico no está vigente.")

    parser=etree.XMLParser(resolve_entities=False,no_network=True,remove_blank_text=False)
    root=etree.fromstring(Path(invoice.xml_path).read_bytes(),parser=parser)

    cert_chain=[cert,*chain]
    signer=SriXAdESSigner(
        claimed_roles=["supplier"],
        data_object_format=XAdESDataObjectFormat(
            Description="Factura electrónica",
            MimeType="text/xml",
        ),
        signature_algorithm=SignatureMethod.RSA_SHA1,
        digest_algorithm=DigestAlgorithm.SHA1,
        c14n_algorithm="http://www.w3.org/TR/2001/REC-xml-c14n-20010315",
    )
    signed=signer.sign(
        root,
        key=key,
        cert=cert_chain,
        reference_uri="#comprobante",
        id_attribute="id",
        always_add_key_value=False,
    )

    cert_pem=cert.public_bytes(serialization.Encoding.PEM)
    verify_config=XAdESSignatureConfiguration(
        signature_methods=list(SignatureMethod),
        digest_algorithms=list(DigestAlgorithm),
    )
    XAdESVerifier().verify(
        signed,
        x509_cert=cert_pem,
        expect_references=3,
        expect_config=verify_config,
    )

    target=Path(invoice.xml_path).with_name(f"{invoice.access_key}_signed.xml")
    target.write_bytes(etree.tostring(signed,encoding="UTF-8",xml_declaration=True,pretty_print=False))
    target.chmod(0o600)

    invoice.signed_xml_path=str(target)
    invoice.status="SIGNED"
    invoice.error_message=None
    return target
