import logging
import traceback
from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.exceptions import (
    GoRetailException,
    NotFoundException,
    UnauthorizedException,
    ForbiddenException,
    ConflictException,
    ValidationException,
    DatabaseException,
    MLModelException,
)

logger = logging.getLogger("go_retail")


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """
    Middleware global de manejo de excepciones.
    Captura errores del dominio y los convierte en respuestas HTTP consistentes.
    Los errores inesperados se loguean sin exponer el stack trace al cliente.
    """

    async def dispatch(self, request: Request, call_next):
        try:
            return await call_next(request)

        except NotFoundException as exc:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"error": "not_found", "message": exc.message},
            )

        except UnauthorizedException as exc:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"error": "unauthorized", "message": exc.message},
                headers={"WWW-Authenticate": "Bearer"},
            )

        except ForbiddenException as exc:
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"error": "forbidden", "message": exc.message},
            )

        except ConflictException as exc:
            return JSONResponse(
                status_code=status.HTTP_409_CONFLICT,
                content={"error": "conflict", "message": exc.message},
            )

        except ValidationException as exc:
            return JSONResponse(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                content={
                    "error": "validation_error",
                    "message": exc.message,
                    "detail": exc.detail,
                },
            )

        except DatabaseException as exc:
            logger.error("Database error: %s | detail: %s", exc.message, exc.detail)
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={"error": "database_error", "message": "Error en base de datos"},
            )

        except MLModelException as exc:
            logger.error("ML model error: %s | detail: %s", exc.message, exc.detail)
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"error": "model_error", "message": exc.message},
            )

        except GoRetailException as exc:
            logger.warning("Domain exception: %s", exc.message)
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"error": "domain_error", "message": exc.message},
            )

        except Exception:
            logger.error("Unexpected error:\n%s", traceback.format_exc())
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "error": "internal_error",
                    "message": "Error interno del servidor",
                },
            )
