import logging
import traceback
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.config.settings import get_settings
from app.config.database import engine
from app.infrastructure.orm.models import Base
from app.api.v1.router import api_router
from app.core.exceptions import (
    NotFoundException, UnauthorizedException, ForbiddenException,
    ConflictException, ValidationException, DatabaseException, MLModelException,
    GoRetailException,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger("go_retail")

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Iniciando Go Retail API v1.0.0")
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Tablas verificadas/creadas en base de datos")
    except Exception as e:
        logger.error("Error creando tablas: %s", e)
    yield
    logger.info("Deteniendo Go Retail API")


app = FastAPI(
    title="Go Retail API",
    description=(
        "**Supply Chain Intelligence API** para retail colombiano.\n\n"
        "## Autenticación\n"
        "Todos los endpoints requieren **Bearer Token JWT** (excepto `/health` y `/api/v1/auth/login`).\n\n"
        "1. Llama `POST /api/v1/auth/login` con username y password\n"
        "2. Usa el `access_token` en: `Authorization: Bearer <token>`\n\n"
        "## Roles\n"
        "- **viewer**: Solo lectura\n"
        "- **analyst**: Lectura + ejecutar modelos\n"
        "- **admin**: Acceso total"
    ),
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

# ── CORS ─────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Exception handlers (más confiables que BaseHTTPMiddleware) ────

@app.exception_handler(NotFoundException)
async def not_found_handler(request: Request, exc: NotFoundException):
    return JSONResponse(status_code=404, content={"detail": exc.message})

@app.exception_handler(UnauthorizedException)
async def unauthorized_handler(request: Request, exc: UnauthorizedException):
    return JSONResponse(
        status_code=401,
        content={"detail": exc.message},
        headers={"WWW-Authenticate": "Bearer"},
    )

@app.exception_handler(ForbiddenException)
async def forbidden_handler(request: Request, exc: ForbiddenException):
    return JSONResponse(status_code=403, content={"detail": exc.message})

@app.exception_handler(ConflictException)
async def conflict_handler(request: Request, exc: ConflictException):
    return JSONResponse(status_code=409, content={"detail": exc.message})

@app.exception_handler(ValidationException)
async def validation_handler(request: Request, exc: ValidationException):
    return JSONResponse(status_code=422, content={"detail": exc.message})

@app.exception_handler(DatabaseException)
async def database_handler(request: Request, exc: DatabaseException):
    logger.error("Database error: %s | %s", exc.message, exc.detail)
    detail = exc.message if not exc.detail else f"{exc.message}: {exc.detail}"
    return JSONResponse(status_code=503, content={"detail": detail})

@app.exception_handler(MLModelException)
async def ml_handler(request: Request, exc: MLModelException):
    logger.error("ML error: %s | %s", exc.message, exc.detail)
    detail = exc.message if not exc.detail else f"{exc.message}: {exc.detail}"
    return JSONResponse(status_code=500, content={"detail": detail})

@app.exception_handler(GoRetailException)
async def domain_handler(request: Request, exc: GoRetailException):
    return JSONResponse(status_code=400, content={"detail": exc.message})

@app.exception_handler(Exception)
async def generic_handler(request: Request, exc: Exception):
    logger.error("Error inesperado en %s:\n%s", request.url, traceback.format_exc())
    return JSONResponse(status_code=500, content={"detail": "Error interno del servidor"})

# ── Rutas ────────────────────────────────────────────────────────
app.include_router(api_router, prefix="/api/v1")


@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "healthy", "version": "1.0.0"}
