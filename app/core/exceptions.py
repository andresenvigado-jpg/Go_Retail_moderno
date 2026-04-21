from typing import Any, Optional


class GoRetailException(Exception):
    """Excepción base del dominio Go Retail."""

    def __init__(self, message: str, detail: Optional[Any] = None):
        self.message = message
        self.detail = detail
        super().__init__(self.message)


class NotFoundException(GoRetailException):
    """Recurso no encontrado."""

    def __init__(self, resource: str, identifier: Any = None):
        msg = f"{resource} no encontrado"
        if identifier is not None:
            msg += f": {identifier}"
        super().__init__(msg)


class UnauthorizedException(GoRetailException):
    """Credenciales inválidas o token expirado."""

    def __init__(self, message: str = "No autorizado"):
        super().__init__(message)


class ForbiddenException(GoRetailException):
    """Acceso denegado por permisos insuficientes."""

    def __init__(self, message: str = "Acceso denegado"):
        super().__init__(message)


class ConflictException(GoRetailException):
    """Conflicto con el estado actual del recurso."""

    def __init__(self, message: str):
        super().__init__(message)


class ValidationException(GoRetailException):
    """Error de validación de datos de entrada."""

    def __init__(self, message: str, detail: Optional[Any] = None):
        super().__init__(message, detail)


class DatabaseException(GoRetailException):
    """Error en operaciones de base de datos."""

    def __init__(self, message: str = "Error en base de datos", detail: Optional[Any] = None):
        super().__init__(message, detail)


class MLModelException(GoRetailException):
    """Error durante la ejecución de un modelo ML."""

    def __init__(self, model: str, detail: Optional[Any] = None):
        super().__init__(f"Error ejecutando modelo {model}", detail)
