from typing import Generator
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.core.security import decode_token
from app.core.exceptions import UnauthorizedException, ForbiddenException
from app.infrastructure.orm.models import UsuarioORM

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> UsuarioORM:
    """
    Extrae y valida el usuario desde el JWT Bearer token.
    Inyectable en cualquier endpoint protegido.
    """
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token inválido o expirado",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_token(token)
        if payload.get("type") != "access":
            raise credentials_error
        username: str = payload.get("sub")
        if not username:
            raise credentials_error
    except JWTError:
        raise credentials_error

    user = db.query(UsuarioORM).filter(UsuarioORM.username == username).first()
    if not user or not user.activo:
        raise credentials_error
    return user


def require_roles(*roles: str):
    """
    Factory de dependencia para control de acceso basado en rol.
    Uso: Depends(require_roles("admin", "analyst"))
    """
    def role_checker(current_user: UsuarioORM = Depends(get_current_user)) -> UsuarioORM:
        if current_user.rol not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Se requiere uno de los roles: {', '.join(roles)}",
            )
        return current_user

    return role_checker


# Dependencias reutilizables por rol
require_admin = require_roles("admin")
require_analyst = require_roles("admin", "analyst")
require_viewer = require_roles("admin", "analyst", "viewer")
