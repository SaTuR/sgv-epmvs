import argparse
from sqlalchemy import select
from app.core.security import hash_password
from app.db import SessionLocal
from app.models import Role, User
from app.seed import run_seed

def create_admin(args):
    run_seed()
    db = SessionLocal()
    try:
        if db.scalar(select(User).where(User.email == args.email.lower())):
            raise SystemExit("Ya existe un usuario con ese correo.")
        role = db.scalar(select(Role).where(Role.name == "Administrador"))
        user = User(
            identification=args.identification, first_name=args.first_name, last_name=args.last_name,
            email=args.email.lower(), password_hash=hash_password(args.password), roles=[role],
        )
        db.add(user); db.commit()
        print(f"Administrador creado: {user.email}")
    finally:
        db.close()

def main():
    parser = argparse.ArgumentParser(prog="sgv-epmvs")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("seed")
    p = sub.add_parser("create-admin")
    p.add_argument("--identification", default=None)
    p.add_argument("--first-name", required=True)
    p.add_argument("--last-name", required=True)
    p.add_argument("--email", required=True)
    p.add_argument("--password", required=True)
    args = parser.parse_args()
    run_seed() if args.command == "seed" else create_admin(args)

if __name__ == "__main__":
    main()
