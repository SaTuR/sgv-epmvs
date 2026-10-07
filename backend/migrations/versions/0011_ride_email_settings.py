"""Parametric RIDE and email settings

Revision ID: 0011_ride_email_settings
Revises: 0010_sri_web_services
Create Date: 2026-10-07
"""
from alembic import op
import sqlalchemy as sa

revision="0011_ride_email_settings"
down_revision="0010_sri_web_services"
branch_labels=None
depends_on=None

def upgrade():
    # Parámetros fiscales configurables para factura
    op.add_column("system_settings",sa.Column("sri_tax_code",sa.String(length=2),nullable=False,server_default="2"))
    op.add_column("system_settings",sa.Column("sri_tax_percentage_code",sa.String(length=4),nullable=False,server_default="6"))
    op.add_column("system_settings",sa.Column("sri_tax_rate",sa.Numeric(7,4),nullable=False,server_default="0"))
    op.add_column("system_settings",sa.Column("sri_payment_method_code",sa.String(length=2),nullable=False,server_default="20"))
    op.add_column("system_settings",sa.Column("sri_software_provider_ruc",sa.String(length=13),nullable=True))

    # RIDE
    op.add_column("system_settings",sa.Column("ride_title",sa.String(length=180),nullable=False,server_default="RIDE - FACTURA ELECTRÓNICA"))
    op.add_column("system_settings",sa.Column("ride_subtitle",sa.String(length=255),nullable=True))
    op.add_column("system_settings",sa.Column("ride_footer",sa.String(length=500),nullable=False,server_default="Documento generado por el Sistema de Gestión y Venta"))
    op.add_column("system_settings",sa.Column("ride_additional_text",sa.Text(),nullable=True))
    op.add_column("system_settings",sa.Column("ride_page_size",sa.String(length=20),nullable=False,server_default="A4"))
    op.add_column("system_settings",sa.Column("ride_show_logo",sa.Boolean(),nullable=False,server_default=sa.true()))
    op.add_column("system_settings",sa.Column("ride_logo_path",sa.String(length=500),nullable=True))
    op.add_column("system_settings",sa.Column("ride_show_qr",sa.Boolean(),nullable=False,server_default=sa.true()))
    op.add_column("system_settings",sa.Column("ride_qr_size_mm",sa.Integer(),nullable=False,server_default="28"))
    op.add_column("system_settings",sa.Column("ride_qr_content_template",sa.String(length=800),nullable=False,server_default="{access_key}"))
    op.add_column("system_settings",sa.Column("ride_primary_hex",sa.String(length=7),nullable=False,server_default="#3A6C32"))

    # Email
    op.add_column("system_settings",sa.Column("invoice_email_enabled",sa.Boolean(),nullable=False,server_default=sa.false()))
    op.add_column("system_settings",sa.Column("invoice_email_send_on_authorization",sa.Boolean(),nullable=False,server_default=sa.false()))
    op.add_column("system_settings",sa.Column("smtp_host",sa.String(length=255),nullable=True))
    op.add_column("system_settings",sa.Column("smtp_port",sa.Integer(),nullable=False,server_default="587"))
    op.add_column("system_settings",sa.Column("smtp_security",sa.String(length=20),nullable=False,server_default="STARTTLS"))
    op.add_column("system_settings",sa.Column("smtp_username",sa.String(length=255),nullable=True))
    op.add_column("system_settings",sa.Column("smtp_password_encrypted",sa.Text(),nullable=True))
    op.add_column("system_settings",sa.Column("smtp_sender_email",sa.String(length=255),nullable=True))
    op.add_column("system_settings",sa.Column("smtp_sender_name",sa.String(length=180),nullable=True))
    op.add_column("system_settings",sa.Column("invoice_email_subject_template",sa.String(length=500),nullable=False,server_default="Factura electrónica {document_number}"))
    op.add_column("system_settings",sa.Column("invoice_email_body_template",sa.Text(),nullable=False,server_default="Estimado/a {customer_name}, adjuntamos su factura electrónica {document_number}."))
    op.add_column("system_settings",sa.Column("invoice_email_attach_ride",sa.Boolean(),nullable=False,server_default=sa.true()))
    op.add_column("system_settings",sa.Column("invoice_email_attach_xml",sa.Boolean(),nullable=False,server_default=sa.true()))
    op.add_column("system_settings",sa.Column("invoice_email_cc",sa.Text(),nullable=True))
    op.add_column("system_settings",sa.Column("invoice_email_bcc",sa.Text(),nullable=True))
    op.add_column("system_settings",sa.Column("invoice_email_retries",sa.Integer(),nullable=False,server_default="3"))
    op.add_column("system_settings",sa.Column("invoice_email_timeout_seconds",sa.Integer(),nullable=False,server_default="20"))

def downgrade():
    for name in [
        "invoice_email_timeout_seconds","invoice_email_retries","invoice_email_bcc","invoice_email_cc",
        "invoice_email_attach_xml","invoice_email_attach_ride","invoice_email_body_template",
        "invoice_email_subject_template","smtp_sender_name","smtp_sender_email",
        "smtp_password_encrypted","smtp_username","smtp_security","smtp_port","smtp_host",
        "invoice_email_send_on_authorization","invoice_email_enabled",
        "ride_primary_hex","ride_qr_content_template","ride_qr_size_mm","ride_show_qr",
        "ride_logo_path","ride_show_logo","ride_page_size","ride_additional_text",
        "ride_footer","ride_subtitle","ride_title",
        "sri_software_provider_ruc","sri_payment_method_code","sri_tax_rate",
        "sri_tax_percentage_code","sri_tax_code"
    ]:
        op.drop_column("system_settings",name)
