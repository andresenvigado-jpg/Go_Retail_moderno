from datetime import timedelta
from app.config.settings import get_settings
from app.core.security import (
    hash_password, verify_password,
    create_access_token, create_refresh_token, decode_token,
)
from app.core.exceptions import (
    UnauthorizedException, ConflictException, NotFoundException,
)
from app.domain.entities.user import User, UserRole
from app.domain.interfaces.i_auth_repository import IAuthRepository
from app.application.dtos.auth_dto import (
    LoginRequest, RegisterRequest, TokenResponse, UserResponse,
)
from jose import JWTError

settings = get_settings()


class LoginUseCase:
    """Autentica un usuario y retorna JWT de acceso + refresh."""

    def __init__(self, repo: IAuthRepository):
        self._repo = repo

    def execute(self, request: LoginRequest) -> TokenResponse:
        user = self._repo.get_by_username(request.username)
        if not user or not verify_password(request.password, user.hashed_password):
            raise UnauthorizedException("Credenciales incorrectas")
        if not user.activo:
            raise UnauthorizedException("Usuario desactivado")

        self._repo.update_last_access(user.id)

        token_data = {"sub": user.username, "rol": user.rol.value}
        return TokenResponse(
            access_token=create_access_token(token_data),
            refresh_token=create_refresh_token(token_data),
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )


class RegisterUseCase:
    """Registra un nuevo usuario (solo admin puede asignar roles elevados)."""

    def __init__(self, repo: IAuthRepository):
        self._repo = repo

    def execute(self, request: RegisterRequest) -> UserResponse:
        if self._repo.username_exists(request.username):
            raise ConflictException(f"El username '{request.username}' ya está en uso")
        if self._repo.email_exists(request.email):
            raise ConflictException(f"El email '{request.email}' ya está registrado")

        new_user = User(
            username=request.username,
            email=request.email,
            hashed_password=hash_password(request.password),
            rol=request.rol,
        )
        saved = self._repo.create(new_user)
        return UserResponse(
            id=saved.id,
            username=saved.username,
            email=saved.email,
            rol=saved.rol,
            activo=saved.activo,
            creado_en=saved.creado_en,
            ultimo_acceso=saved.ultimo_acceso,
        )


class RefreshTokenUseCase:
    """Renueva el access token usando el refresh token."""

    def __init__(self, repo: IAuthRepository):
        self._repo = repo

    def execute(self, refresh_token: str) -> TokenResponse:
        try:
            payload = decode_token(refresh_token)
            if payload.get("type") != "refresh":
                raise UnauthorizedException("Token de tipo incorrecto")
            username: str = payload.get("sub")
        except JWTError:
            raise UnauthorizedException("Refresh token inválido o expirado")

        user = self._repo.get_by_username(username)
        if not user or not user.activo:
            raise UnauthorizedException("Usuario no encontrado o desactivado")

        token_data = {"sub": user.username, "rol": user.rol.value}
        return TokenResponse(
            access_token=create_access_token(token_data),
            refresh_token=create_refresh_token(token_data),
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )
