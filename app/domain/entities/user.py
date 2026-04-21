from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from enum import Enum


class UserRole(str, Enum):
    ADMIN = "admin"
    ANALYST = "analyst"
    VIEWER = "viewer"


@dataclass
class User:
    """Entidad de dominio Usuario — sin acoplamiento a ORM ni framework."""
    username: str
    email: str
    hashed_password: str
    rol: UserRole = UserRole.VIEWER
    activo: bool = True
    id: Optional[int] = None
    creado_en: Optional[datetime] = None
    ultimo_acceso: Optional[datetime] = None

    def is_admin(self) -> bool:
        return self.rol == UserRole.ADMIN

    def can_run_models(self) -> bool:
        return self.rol in (UserRole.ADMIN, UserRole.ANALYST)
