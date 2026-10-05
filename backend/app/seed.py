from sqlalchemy import select
from app.db import SessionLocal
from app.models import Permission, Project, ProjectStage, PropertyStatus, Role

PERMISSIONS = [
    ("system.admin","Administración total"),("dashboard.view","Ver dashboard"),("users.manage","Administrar usuarios"),
    ("roles.manage","Administrar roles y permisos"),("customers.manage","Administrar clientes"),
    ("projects.manage","Administrar proyectos y etapas"),("properties.manage","Administrar predios"),
    ("sales.manage","Administrar ventas y reservas"),("payments.manage","Registrar y administrar pagos"),
    ("receivables.view","Consultar cuentas por cobrar"),("reports.view","Consultar reportes"),("audit.view","Consultar auditoría"),
]
ROLES = [
    ("Administrador","Acceso completo"),("Comercial / Ventas","Clientes, reservas y ventas"),
    ("Recaudación / Tesorería","Pagos y certificados"),("Financiero / Cartera","Cartera y reportes"),
    ("Consulta / Gerencia","Consulta ejecutiva"),
]
STATUSES = [
    ("AVAILABLE","Disponible",10),("RESERVED","Reservado",20),("CONFIRMED","Compra confirmada",30),
    ("PAYING","En proceso de pago",40),("PAID","Pagado",50),("AWARDED","Adjudicado",60),
    ("BLOCKED","Bloqueado",70),("CANCELLED","Anulado",80),
]

def run_seed():
    db=SessionLocal()
    try:
        permission_objects=[]
        for code,name in PERMISSIONS:
            p=db.scalar(select(Permission).where(Permission.code==code))
            if not p: p=Permission(code=code,name=name); db.add(p); db.flush()
            permission_objects.append(p)
        for name,description in ROLES:
            role=db.scalar(select(Role).where(Role.name==name))
            if not role: role=Role(name=name,description=description); db.add(role); db.flush()
            if name=="Administrador": role.permissions=permission_objects
        for code,name,sort_order in STATUSES:
            s=db.scalar(select(PropertyStatus).where(PropertyStatus.code==code))
            if not s: db.add(PropertyStatus(code=code,name=name,sort_order=sort_order))
        project=db.scalar(select(Project).where(Project.name=="San Joaquín"))
        if not project:
            project=Project(name="San Joaquín",description="Proyecto habitacional inicial del SGV EPMVS")
            project.stages=[ProjectStage(name="Etapa 1"),ProjectStage(name="Etapa 2")]; db.add(project)
        db.commit(); print("Seed inicial aplicado correctamente.")
    finally: db.close()

if __name__=="__main__": run_seed()
