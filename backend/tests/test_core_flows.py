import uuid
from datetime import date, timedelta
from sqlalchemy import select

from app.db import SessionLocal
from app.models import Installment, Permission, Property, Role, Sale
from tests.conftest import create_customer_and_property, create_user_with_permissions, login_headers


def test_health(client):
    r=client.get("/api/health")
    assert r.status_code==200
    assert r.json()["database"]=="ok"


def test_wrong_password_is_rejected(client):
    r=client.post("/api/auth/login",json={"email":"nobody@example.com","password":"wrong"})
    assert r.status_code==401


def test_user_without_permission_cannot_manage_users(client):
    email="qa-noperms-"+uuid.uuid4().hex[:6]+"@example.com"
    password="QaPass123!"
    create_user_with_permissions(email,password,[])
    headers=login_headers(client,email,password)
    r=client.get("/api/security/users",headers=headers)
    assert r.status_code==403


def test_double_reservation_is_rejected(client,admin_headers):
    customer_id,property_id=create_customer_and_property()
    payload={"customer_id":customer_id,"property_id":property_id,"reservation_date":str(date.today()),"expires_on":str(date.today()+timedelta(days=3))}
    r1=client.post("/api/reservations",json=payload,headers=admin_headers)
    assert r1.status_code==200, r1.text
    r2=client.post("/api/reservations",json=payload,headers=admin_headers)
    assert r2.status_code==409


def test_release_requires_specific_permission(client):
    email="qa-sales-"+uuid.uuid4().hex[:6]+"@example.com"
    password="QaPass123!"
    _,role_id=create_user_with_permissions(email,password,["sales.manage"])
    headers=login_headers(client,email,password)
    customer_id,property_id=create_customer_and_property()
    r=client.post("/api/reservations",json={"customer_id":customer_id,"property_id":property_id},headers=headers)
    assert r.status_code==200, r.text
    reservation_id=r.json()["id"]

    denied=client.post(f"/api/reservations/{reservation_id}/cancel",headers=headers)
    assert denied.status_code==403

    db=SessionLocal()
    try:
        role=db.get(Role,uuid.UUID(role_id))
        permission=db.scalar(select(Permission).where(Permission.code=="reservations.release"))
        role.permissions.append(permission)
        db.commit()
    finally:
        db.close()

    allowed=client.post(f"/api/reservations/{reservation_id}/cancel",headers=headers)
    assert allowed.status_code==200, allowed.text
    db=SessionLocal()
    try:
        prop=db.get(Property,uuid.UUID(property_id))
        assert prop.status.code=="AVAILABLE"
    finally:
        db.close()


def test_full_down_payment_creates_no_zero_installments(client,admin_headers):
    customer_id,property_id=create_customer_and_property()
    payload={
        "customer_id":customer_id,
        "property_id":property_id,
        "sale_price":10000,
        "down_payment":10000,
        "installment_count":12,
        "frequency":"MONTHLY",
        "first_due_date":str(date.today()+timedelta(days=30)),
    }
    r=client.post("/api/sales",json=payload,headers=admin_headers)
    assert r.status_code==200, r.text
    sale_id=r.json()["id"]
    db=SessionLocal()
    try:
        sale=db.get(Sale,uuid.UUID(sale_id))
        assert sale.installment_count==0
        assert len(sale.installments)==0
        assert sale.property_id==uuid.UUID(property_id)
        assert sale.financed_amount==0
        prop=db.get(Property,uuid.UUID(property_id))
        assert prop.status.code=="PAID"
    finally:
        db.close()


def test_payment_cannot_exceed_balance(client,admin_headers):
    customer_id,property_id=create_customer_and_property()
    sale=client.post("/api/sales",json={
        "customer_id":customer_id,
        "property_id":property_id,
        "sale_price":10000,
        "down_payment":1000,
        "installment_count":9,
        "frequency":"MONTHLY",
        "first_due_date":str(date.today()+timedelta(days=30)),
    },headers=admin_headers)
    assert sale.status_code==200, sale.text
    sale_id=sale.json()["id"]
    r=client.post("/api/payments",json={
        "sale_id":sale_id,
        "payment_date":str(date.today()),
        "amount":9000.01,
        "payment_method":"TRANSFERENCIA",
    },headers=admin_headers)
    assert r.status_code==400


def test_collections_report_includes_down_payment(client,admin_headers):
    customer_id,property_id=create_customer_and_property()
    sale=client.post("/api/sales",json={
        "customer_id":customer_id,
        "property_id":property_id,
        "sale_price":10000,
        "down_payment":2500,
        "installment_count":5,
        "frequency":"MONTHLY",
        "first_due_date":str(date.today()+timedelta(days=30)),
    },headers=admin_headers)
    assert sale.status_code==200, sale.text
    rows=client.get("/api/reports/collections",headers=admin_headers)
    assert rows.status_code==200, rows.text
    assert any(x["method"]=="ENTRADA" and abs(x["amount"]-2500)<0.001 for x in rows.json())


def test_document_direct_download_requires_permission(client,admin_headers):
    customer_id,property_id=create_customer_and_property()
    sale=client.post("/api/sales",json={
        "customer_id":customer_id,
        "property_id":property_id,
        "sale_price":10000,
        "down_payment":1000,
        "installment_count":9,
        "frequency":"MONTHLY",
        "first_due_date":str(date.today()+timedelta(days=30)),
    },headers=admin_headers)
    assert sale.status_code==200
    sale_id=sale.json()["id"]

    email="qa-docless-"+uuid.uuid4().hex[:6]+"@example.com"
    password="QaPass123!"
    create_user_with_permissions(email,password,[])
    headers=login_headers(client,email,password)

    r=client.get(f"/api/sales/{sale_id}/statement.pdf",headers=headers)
    assert r.status_code==403


def test_public_verification_unknown_code_returns_404(client):
    r=client.get("/api/public/documents/"+str(uuid.uuid4()))
    assert r.status_code==404


def test_property_total_is_recalculated_server_side(client,admin_headers):
    db=SessionLocal()
    try:
        from app.models import Project, ProjectStage, Block
        project=db.scalar(select(Project).where(Project.name=="San Joaquín"))
        stage=db.scalar(select(ProjectStage).where(ProjectStage.project_id==project.id).order_by(ProjectStage.name))
        suffix=uuid.uuid4().hex[:8]
        block=Block(stage_id=stage.id,name="QA-CALC-"+suffix)
        db.add(block);db.commit();db.refresh(block)
        block_id=str(block.id)
    finally:
        db.close()

    payload={
        "block_id":block_id,
        "status_code":"AVAILABLE",
        "code":"QA-CALC-"+uuid.uuid4().hex[:8],
        "lot_number":uuid.uuid4().hex[:6],
        "cadastral_key":"CAT-QA-"+uuid.uuid4().hex[:6],
        "area_m2":123.45,
        "price_per_m2":87.65,
        "total_price":1,
        "location_reference":"Referencia QA",
        "notes":"Prueba de cálculo automático",
    }
    r=client.post("/api/properties",json=payload,headers=admin_headers)
    assert r.status_code==200, r.text

    db=SessionLocal()
    try:
        prop=db.get(Property,uuid.UUID(r.json()["id"]))
        assert float(prop.total_price)==round(123.45*87.65,2)
    finally:
        db.close()


def test_customer_required_fields_are_enforced(client,admin_headers):
    r=client.post("/api/customers",json={
        "identification_type":"CEDULA",
        "identification":"0999999999",
        "first_name":"QA",
        "last_name":"Sin Datos"
    },headers=admin_headers)
    assert r.status_code==422


def test_property_required_fields_are_enforced(client,admin_headers):
    db=SessionLocal()
    try:
        from app.models import Project, ProjectStage, Block
        project=db.scalar(select(Project).where(Project.name=="San Joaquín"))
        stage=db.scalar(select(ProjectStage).where(ProjectStage.project_id==project.id).order_by(ProjectStage.name))
        block=Block(stage_id=stage.id,name="QA-REQ-"+uuid.uuid4().hex[:8])
        db.add(block);db.commit();db.refresh(block)
        block_id=str(block.id)
    finally:
        db.close()

    r=client.post("/api/properties",json={
        "block_id":block_id,
        "status_code":"AVAILABLE",
        "code":"QA-REQ-"+uuid.uuid4().hex[:8],
        "lot_number":"001",
        "area_m2":100,
        "price_per_m2":100,
        "total_price":10000
    },headers=admin_headers)
    assert r.status_code==422


def test_settings_requires_system_admin(client):
    email="qa-settings-"+uuid.uuid4().hex[:6]+"@example.com"
    password="QaPass123!"
    create_user_with_permissions(email,password,["sales.manage"])
    headers=login_headers(client,email,password)
    r=client.get("/api/settings",headers=headers)
    assert r.status_code==403


def test_admin_can_read_and_update_settings(client,admin_headers):
    current=client.get("/api/settings",headers=admin_headers)
    assert current.status_code==200, current.text
    original=current.json()

    payload={
        "institution_name":original["institution_name"],
        "tax_id":original.get("tax_id"),
        "address":original.get("address"),
        "phone":original.get("phone"),
        "email":original.get("email"),
        "city":original["city"],
        "province":original["province"],
        "reservation_default_days":7,
        "currency_symbol":"$",
        "public_base_url":original["public_base_url"],
        "document_footer":original["document_footer"],
        "timezone":original["timezone"],
    }
    saved=client.put("/api/settings",json=payload,headers=admin_headers)
    assert saved.status_code==200, saved.text
    assert saved.json()["reservation_default_days"]==7

    runtime=client.get("/api/settings/runtime",headers=admin_headers)
    assert runtime.status_code==200, runtime.text
    assert runtime.json()["reservation_default_days"]==7

    restore={k:original.get(k) for k in payload.keys()}
    restored=client.put("/api/settings",json=restore,headers=admin_headers)
    assert restored.status_code==200, restored.text
