from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, field_validator
from app.domain.entities.user import UserRole


class LoginRequest(BaseModel):
    username: str
    password: str


class RegisterRequest(BaseModel):
    username: str
    email: EmailStr
    password: str
    rol: UserRole = UserRole.VIEWER

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("La contraseña debe tener al menos 8 caracteres")
        return v

    @field_validator("username")
    @classmethod
    def username_format(cls, v: str) -> str:
        v = v.strip().lower()
        if len(v) < 3:
            raise ValueError("El username debe tener al menos 3 caracteres")
        if not v.replace("_", "").replace("-", "").isalnum():
            raise ValueError("El username solo puede contener letras, números, _ y -")
        return v


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # segundos


class RefreshRequest(BaseModel):
    refresh_token: str


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    rol: UserRole
    activo: bool
    creado_en: Optional[datetime]
    ultimo_acceso: Optional[datetime]

    model_config = {"from_attributes": True}
