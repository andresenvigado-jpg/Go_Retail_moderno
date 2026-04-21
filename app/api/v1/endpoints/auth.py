from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.core.dependencies import get_current_user, require_admin
from app.infrastructure.orm.models import UsuarioORM
from app.infrastructure.repositories.auth_repository import AuthRepository
from app.application.use_cases.auth_use_cases import (
    LoginUseCase, RegisterUseCase, RefreshTokenUseCase,
)
from app.application.dtos.auth_dto import (
    LoginRequest, RegisterRequest, TokenResponse,
    RefreshRequest, UserResponse,
)

router = APIRouter(prefix="/auth", tags=["Autenticación"])


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Iniciar sesión",
    description="Autentica con username y password. Retorna access_token (30 min) y refresh_token (7 días).",
)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    repo = AuthRepository(db)
    request = LoginRequest(username=form_data.username, password=form_data.password)
    return LoginUseCase(repo).execute(request)


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar usuario",
    description="Solo admins pueden registrar nuevos usuarios con rol analyst o admin.",
    dependencies=[Depends(require_admin)],
)
def register(
    request: RegisterRequest,
    db: Session = Depends(get_db),
):
    repo = AuthRepository(db)
    return RegisterUseCase(repo).execute(request)


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Renovar token",
    description="Usa el refresh_token para obtener un nuevo access_token.",
)
def refresh(
    request: RefreshRequest,
    db: Session = Depends(get_db),
):
    repo = AuthRepository(db)
    return RefreshTokenUseCase(repo).execute(request.refresh_token)


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Mi perfil",
    description="Retorna la información del usuario autenticado.",
)
def me(current_user: UsuarioORM = Depends(get_current_user)):
    return UserResponse(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        rol=current_user.rol,
        activo=current_user.activo,
        creado_en=current_user.creado_en,
        ultimo_acceso=current_user.ultimo_acceso,
    )
