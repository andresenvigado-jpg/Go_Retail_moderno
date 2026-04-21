from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.domain.entities.user import User, UserRole
from app.domain.interfaces.i_auth_repository import IAuthRepository
from app.infrastructure.orm.models import UsuarioORM
from app.core.exceptions import DatabaseException


class AuthRepository(IAuthRepository):
    """Implementación PostgreSQL del repositorio de autenticación."""

    def __init__(self, db: Session):
        self._db = db

    def _to_entity(self, orm: UsuarioORM) -> User:
        return User(
            id=orm.id,
            username=orm.username,
            email=orm.email,
            hashed_password=orm.hashed_password,
            rol=UserRole(orm.rol),
            activo=orm.activo,
            creado_en=orm.creado_en,
            ultimo_acceso=orm.ultimo_acceso,
        )

    def get_by_username(self, username: str) -> Optional[User]:
        try:
            orm = self._db.query(UsuarioORM).filter(
                UsuarioORM.username == username
            ).first()
            return self._to_entity(orm) if orm else None
        except SQLAlchemyError as e:
            raise DatabaseException(detail=str(e))

    def get_by_id(self, user_id: int) -> Optional[User]:
        try:
            orm = self._db.query(UsuarioORM).filter(UsuarioORM.id == user_id).first()
            return self._to_entity(orm) if orm else None
        except SQLAlchemyError as e:
            raise DatabaseException(detail=str(e))

    def create(self, user: User) -> User:
        try:
            orm = UsuarioORM(
                username=user.username,
                email=user.email,
                hashed_password=user.hashed_password,
                rol=user.rol.value,
                activo=user.activo,
            )
            self._db.add(orm)
            self._db.commit()
            self._db.refresh(orm)
            return self._to_entity(orm)
        except SQLAlchemyError as e:
            self._db.rollback()
            raise DatabaseException(detail=str(e))

    def update_last_access(self, user_id: int) -> None:
        try:
            self._db.query(UsuarioORM).filter(UsuarioORM.id == user_id).update(
                {"ultimo_acceso": datetime.now(timezone.utc)}
            )
            self._db.commit()
        except SQLAlchemyError as e:
            self._db.rollback()
            raise DatabaseException(detail=str(e))

    def username_exists(self, username: str) -> bool:
        return self._db.query(
            self._db.query(UsuarioORM).filter(UsuarioORM.username == username).exists()
        ).scalar()

    def email_exists(self, email: str) -> bool:
        return self._db.query(
            self._db.query(UsuarioORM).filter(UsuarioORM.email == email).exists()
        ).scalar()
