from typing import Optional, List, Dict, Any
import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.domain.interfaces.i_analytics_repository import IAnalyticsRepository
from app.infrastructure.orm.models import (
    RentabilidadSKUORM, RotacionSKUORM, EficienciaReposicionORM
)
from app.core.exceptions import DatabaseException
from app.infrastructure.repositories.inventory_repository import _df_to_records


class AnalyticsRepository(IAnalyticsRepository):
    """Implementación PostgreSQL para análisis de negocio."""

    def __init__(self, db: Session):
        self._db = db

    def get_rentability(self, sku_id: Optional[str] = None, limit: int = 100) -> pd.DataFrame:
        try:
            q = self._db.query(RentabilidadSKUORM)
            if sku_id:
                q = q.filter(RentabilidadSKUORM.sku_id == sku_id)
            rows = q.order_by(RentabilidadSKUORM.indice_rentabilidad.desc()).limit(limit).all()
            if not rows:
                return pd.DataFrame()
            return pd.DataFrame([{
                "sku_id": r.sku_id,
                "tienda_id": r.tienda_id,
                "margen_porcentual": r.margen_porcentual,
                "rentabilidad_total": r.rentabilidad_total,
                "indice_rentabilidad": r.indice_rentabilidad,
                "clasificacion": r.clasificacion,
            } for r in rows])
        except SQLAlchemyError as e:
            raise DatabaseException(detail=str(e))

    def get_rotation(self, sku_id: Optional[str] = None, limit: int = 100) -> pd.DataFrame:
        try:
            q = self._db.query(RotacionSKUORM)
            if sku_id:
                q = q.filter(RotacionSKUORM.sku_id == sku_id)
            rows = q.order_by(RotacionSKUORM.indice_velocidad.desc()).limit(limit).all()
            if not rows:
                return pd.DataFrame()
            return pd.DataFrame([{
                "sku_id": r.sku_id,
                "tienda_id": r.tienda_id,
                "tasa_rotacion_anual": r.tasa_rotacion_anual,
                "dsi": r.dsi,
                "frecuencia_venta": r.frecuencia_venta,
                "indice_velocidad": r.indice_velocidad,
                "clasificacion": r.clasificacion,
            } for r in rows])
        except SQLAlchemyError as e:
            raise DatabaseException(detail=str(e))

    def get_efficiency(self, store_id: Optional[str] = None) -> pd.DataFrame:
        try:
            q = self._db.query(EficienciaReposicionORM)
            if store_id:
                q = q.filter(EficienciaReposicionORM.tienda_id == store_id)
            rows = q.order_by(EficienciaReposicionORM.indice_eficiencia.desc()).all()
            if not rows:
                return pd.DataFrame()
            return pd.DataFrame([{
                "tienda_id": r.tienda_id,
                "cobertura_reposicion": r.cobertura_reposicion,
                "tasa_devolucion": r.tasa_devolucion,
                "eficiencia_skus": r.eficiencia_skus,
                "indice_eficiencia": r.indice_eficiencia,
                "clasificacion": r.clasificacion,
            } for r in rows])
        except SQLAlchemyError as e:
            raise DatabaseException(detail=str(e))

    def save_rentability(self, df: pd.DataFrame) -> int:
        try:
            self._db.query(RentabilidadSKUORM).delete()
            self._db.bulk_insert_mappings(RentabilidadSKUORM, _df_to_records(df))
            self._db.commit()
            return len(df)
        except SQLAlchemyError as e:
            self._db.rollback()
            raise DatabaseException(message=f"save_rentability: {e.__class__.__name__}: {e}", detail=str(e))

    def save_rotation(self, df: pd.DataFrame) -> int:
        try:
            self._db.query(RotacionSKUORM).delete()
            self._db.bulk_insert_mappings(RotacionSKUORM, _df_to_records(df))
            self._db.commit()
            return len(df)
        except SQLAlchemyError as e:
            self._db.rollback()
            raise DatabaseException(message=f"save_rotation: {e.__class__.__name__}: {e}", detail=str(e))

    def save_efficiency(self, df: pd.DataFrame) -> int:
        try:
            self._db.query(EficienciaReposicionORM).delete()
            self._db.bulk_insert_mappings(EficienciaReposicionORM, _df_to_records(df))
            self._db.commit()
            return len(df)
        except SQLAlchemyError as e:
            self._db.rollback()
            raise DatabaseException(message=f"save_efficiency: {e.__class__.__name__}: {e}", detail=str(e))
