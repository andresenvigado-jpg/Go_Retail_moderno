from typing import Optional, List, Dict, Any
import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.domain.interfaces.i_inventory_repository import IInventoryRepository
from app.infrastructure.orm.models import AnomaliaORM, EOQResultadoORM, MonteCarloORM
from app.core.exceptions import DatabaseException


def _df_to_records(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Convierte un DataFrame a lista de dicts con tipos Python nativos.
    Reemplaza NaN/NaT por None y convierte escalares numpy (bool_, float64, int64)
    a sus equivalentes Python para que psycopg2 los acepte sin errores.
    """
    clean = df.where(df.notna(), None)
    records = []
    for rec in clean.to_dict(orient="records"):
        native: Dict[str, Any] = {}
        for k, v in rec.items():
            if v is None:
                native[k] = None
            elif hasattr(v, "item"):        # numpy scalar → Python nativo
                native[k] = v.item()
            else:
                native[k] = v
        records.append(native)
    return records


class InventoryRepository(IInventoryRepository):
    """Implementación PostgreSQL para inventario y modelos relacionados."""

    def __init__(self, db: Session):
        self._db = db

    def get_anomalies(self, tipo: Optional[str] = None, limit: int = 100) -> pd.DataFrame:
        try:
            q = self._db.query(AnomaliaORM)
            if tipo:
                q = q.filter(AnomaliaORM.tipo_anomalia == tipo)
            rows = q.order_by(AnomaliaORM.score_anomalia).limit(limit).all()
            if not rows:
                return pd.DataFrame()
            return pd.DataFrame([{
                "sku_id": r.sku_id,
                "tienda_id": r.tienda_id,
                "tipo_anomalia": r.tipo_anomalia,
                "es_anomalia": r.es_anomalia,
                "score_anomalia": r.score_anomalia,
                "stock_actual": r.stock_actual,
                "cobertura_dias": r.cobertura_dias,
            } for r in rows])
        except SQLAlchemyError as e:
            raise DatabaseException(detail=str(e))

    def get_eoq(self, sku_id: Optional[str] = None, store_id: Optional[str] = None) -> pd.DataFrame:
        try:
            q = self._db.query(EOQResultadoORM)
            if sku_id:
                q = q.filter(EOQResultadoORM.sku_id == sku_id)
            if store_id:
                q = q.filter(EOQResultadoORM.tienda_id == store_id)
            rows = q.all()
            if not rows:
                return pd.DataFrame()
            return pd.DataFrame([{
                "sku_id": r.sku_id,
                "tienda_id": r.tienda_id,
                "eoq": r.eoq,
                "punto_reorden": r.punto_reorden,
                "stock_seguridad": r.stock_seguridad,
                "estado_reposicion": r.estado_reposicion,
                "dias_entre_pedidos": r.dias_entre_pedidos,
                "costo_total_anual": r.costo_total_anual,
            } for r in rows])
        except SQLAlchemyError as e:
            raise DatabaseException(detail=str(e))

    def get_monte_carlo(
        self, sku_id: Optional[str] = None, store_id: Optional[str] = None
    ) -> pd.DataFrame:
        try:
            q = self._db.query(MonteCarloORM)
            if sku_id:
                q = q.filter(MonteCarloORM.sku_id == sku_id)
            if store_id:
                q = q.filter(MonteCarloORM.tienda_id == store_id)
            rows = q.order_by(MonteCarloORM.prob_quiebre.desc()).all()
            if not rows:
                return pd.DataFrame()
            return pd.DataFrame([{
                "sku_id": r.sku_id,
                "tienda_id": r.tienda_id,
                "demanda_p50": r.demanda_p50,
                "demanda_p90": r.demanda_p90,
                "demanda_p95": r.demanda_p95,
                "demanda_p99": r.demanda_p99,
                "prob_quiebre": r.prob_quiebre,
                "stock_recomendado": r.stock_recomendado,
                "nivel_riesgo": r.nivel_riesgo,
            } for r in rows])
        except SQLAlchemyError as e:
            raise DatabaseException(detail=str(e))

    def save_anomalies(self, df: pd.DataFrame) -> int:
        try:
            self._db.query(AnomaliaORM).delete()
            self._db.bulk_insert_mappings(AnomaliaORM, _df_to_records(df))
            self._db.commit()
            return len(df)
        except SQLAlchemyError as e:
            self._db.rollback()
            raise DatabaseException(message=f"save_anomalies: {e.__class__.__name__}: {e}", detail=str(e))

    def save_eoq(self, df: pd.DataFrame) -> int:
        try:
            self._db.query(EOQResultadoORM).delete()
            self._db.bulk_insert_mappings(EOQResultadoORM, _df_to_records(df))
            self._db.commit()
            return len(df)
        except SQLAlchemyError as e:
            self._db.rollback()
            raise DatabaseException(message=f"save_eoq: {e.__class__.__name__}: {e}", detail=str(e))

    def save_monte_carlo(self, df: pd.DataFrame) -> int:
        try:
            self._db.query(MonteCarloORM).delete()
            self._db.bulk_insert_mappings(MonteCarloORM, _df_to_records(df))
            self._db.commit()
            return len(df)
        except SQLAlchemyError as e:
            self._db.rollback()
            raise DatabaseException(message=f"save_monte_carlo: {e.__class__.__name__}: {e}", detail=str(e))
