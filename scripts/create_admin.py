"""
Script de configuración inicial: crea el primer usuario admin.
Ejecutar una sola vez después de desplegar la API.

Uso:
    python scripts/create_admin.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config.database import SessionLocal, engine
from app.infrastructure.orm.models import Base, UsuarioORM
from app.core.security import hash_password


def create_admin(username: str, email: str, password: str) -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        exists = db.query(UsuarioORM).filter(UsuarioORM.username == username).first()
        if exists:
            print(f"⚠️  El usuario '{username}' ya existe.")
            return

        admin = UsuarioORM(
            username=username,
            email=email,
            hashed_password=hash_password(password),
            rol="admin",
            activo=True,
        )
        db.add(admin)
        db.commit()
        print(f"✅ Usuario admin '{username}' creado exitosamente.")
    finally:
        db.close()


if __name__ == "__main__":
    print("\n=== Go Retail API — Crear usuario admin ===\n")
    u = input("Username: ").strip() or "admin"
    e = input("Email: ").strip() or "admin@goretail.com"
    p = input("Password: ").strip() or "Admin123!"
    create_admin(u, e, p)
