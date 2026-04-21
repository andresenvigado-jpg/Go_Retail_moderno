from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from app.config.settings import get_settings

settings = get_settings()

engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,       # Verifica conexión antes de usarla
    pool_size=5,              # Conexiones mínimas en el pool
    max_overflow=10,          # Conexiones adicionales permitidas
    pool_recycle=1800,        # Recicla conexiones cada 30 min
    echo=False,               # True para debug SQL
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    """Generador de sesión de base de datos para inyección de dependencias."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
