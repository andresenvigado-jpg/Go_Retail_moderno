from typing import Optional
import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.domain.interfaces.i_demand_repository import IDemandRepository
from app.infrastructure.orm.models import PronosticoORM, PrediccionLGBMORM
from app.core.exceptions import DatabaseException
from app.infrastructure.repositories.inventory_repository import _df_to_records


class DemandRepository(IDemandRepository):
    """Implementación PostgreSQL para datos de demanda y pronósticos."""

    def __init__(self, db: Session):
        self._db = db

    def get_forecasts(self, sku_id: Optional[str] = None, limit: int = 100) -> pd.DataFrame:
        try:
            q = self._db.query(PronosticoORM)
            if sku_id:
                q = q.filter(PronosticoORM.sku_id == sku_id)
            rows = q.order_by(PronosticoORM.sku_id, PronosticoORM.fecha).limit(limit).all()
            if not rows:
                return pd.DataFrame()
            return pd.DataFrame([{
                "sku_id": r.sku_id,
                "fecha": r.fecha,
                "demanda_estimada": r.demanda_estimada,
                "demanda_minima": r.demanda_minima,
                "demanda_maxima": r.demanda_maxima,
            } for r in rows])
        except SQLAlchemyError as e:
            raise DatabaseException(detail=str(e))

    def get_lgbm_predictions(
        self,
        sku_id: Optional[str] = None,
        store_id: Optional[str] = None,
        limit: int = 100,
    ) -> pd.DataFrame:
        try:
            q = self._db.query(PrediccionLGBMORM)
            if sku_id:
                q = q.filter(PrediccionLGBMORM.sku_id == sku_id)
            if store_id:
                q = q.filter(PrediccionLGBMORM.tienda_id == store_id)
            rows = q.limit(limit).all()
            if not rows:
                return pd.DataFrame()
            return pd.DataFrame([{
                "sku_id": r.sku_id,
                "tienda_id": r.tienda_id,
                "cantidad_real": r.cantidad_real,
                "cantidad_predicha": r.cantidad_predicha,
            } for r in rows])
        except SQLAlchemyError as e:
            raise DatabaseException(detail=str(e))

    def save_forecasts(self, df: pd.DataFrame) -> int:
        try:
            self._db.query(PronosticoORM).delete()
            self._db.bulk_insert_mappings(PronosticoORM, _df_to_records(df))
            self._db.commit()
            return len(df)
        except SQLAlchemyError as e:
            self._db.rollback()
            raise DatabaseException(message=f"save_forecasts: {e.__class__.__name__}: {e}", detail=str(e))

    def save_lgbm_predictions(self, df: pd.DataFrame) -> int:
        try:
            self._db.query(PrediccionLGBMORM).delete()
            self._db.bulk_insert_mappings(PrediccionLGBMORM, _df_to_records(df))
            self._db.commit()
            return len(df)
        except SQLAlchemyError as e:
            self._db.rollback()
            raise DatabaseException(message=f"save_lgbm: {e.__class__.__name__}: {e}", detail=str(e))
