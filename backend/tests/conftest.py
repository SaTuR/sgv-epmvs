import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.main import app
from app.db import SessionLocal
from app.seed import run_seed
from app.core.security import hash_password
from app.models import Block, Customer, Permission, Project, ProjectStage, Property, PropertyStatus, Role, User


@pytest.fixture(scope="session", autouse=True)
def seed_database():
    run_seed()


@pytest.fixture(scope="session")
def client():
    return TestClient(app)


QA_ADMIN_EMAIL="qa-admin@example.com"
QA_ADMIN_PASSWORD="QaAdmin123!"


def ensure_admin():
    db=SessionLocal()
    try:
        role=db.scalar(select(Role).where(Role.name=="Administrador"))
        user=db.scalar(select(User).where(User.identification=="QA-ADMIN"))
        if not user:
            user=User(
                identification="QA-ADMIN",
                first_name="QA",
                last_name="Administrador",
                email=QA_ADMIN_EMAIL,
                password_hash=hash_password(QA_ADMIN_PASSWORD),
                active=True,
                roles=[role],
            )
            db.add(user)
        else:
            user.email=QA_ADMIN_EMAIL
            user.password_hash=hash_password(QA_ADMIN_PASSWORD)
            user.active=True
            user.roles=[role]
        db.commit()
        return user.email
    finally:
        db.close()


@pytest.fixture(scope="session")
def admin_headers(client):
    email=ensure_admin()
    r=client.post("/api/auth/login",json={"email":email,"password":QA_ADMIN_PASSWORD})
    assert r.status_code==200, r.text
    return {"Authorization":"Bearer "+r.json()["access_token"]}


def create_user_with_permissions(email:str,password:str,permission_codes:list[str]):
    db=SessionLocal()
    try:
        role=Role(name="QA-"+uuid.uuid4().hex[:8],description="Rol QA",active=True)
        role.permissions=db.scalars(select(Permission).where(Permission.code.in_(permission_codes))).all() if permission_codes else []
        user=User(
            identification="QA-"+uuid.uuid4().hex[:10],
            first_name="QA",
            last_name="Usuario",
            email=email,
            password_hash=hash_password(password),
            active=True,
            roles=[role],
        )
        db.add_all([role,user]);db.commit();db.refresh(user)
        return str(user.id),str(role.id)
    finally:
        db.close()


def login_headers(client,email,password):
    r=client.post("/api/auth/login",json={"email":email,"password":password})
    assert r.status_code==200, r.text
    return {"Authorization":"Bearer "+r.json()["access_token"]}


def create_customer_and_property():
    db=SessionLocal()
    try:
        suffix=uuid.uuid4().hex[:8]
        project=db.scalar(select(Project).where(Project.name=="San Joaquín"))
        stage=db.scalar(select(ProjectStage).where(ProjectStage.project_id==project.id).order_by(ProjectStage.name))
        block=Block(stage_id=stage.id,name="QA-"+suffix)
        customer=Customer(
            identification="QA-CI-"+suffix,
            first_name="Cliente",
            last_name="QA "+suffix,
            email=f"qa-{suffix}@example.com",
        )
        available=db.scalar(select(PropertyStatus).where(PropertyStatus.code=="AVAILABLE"))
        prop=Property(
            block=block,
            status_id=available.id,
            code="QA-PROP-"+suffix,
            lot_number=suffix,
            area_m2=100,
            price_per_m2=100,
            total_price=10000,
        )
        db.add_all([block,customer,prop]);db.commit()
        return str(customer.id),str(prop.id)
    finally:
        db.close()
