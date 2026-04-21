from typing import List, Optional
import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.domain.entities.product import Product
from app.domain.entities.store import Store
from app.domain.interfaces.i_product_repository import IProductRepository
from app.infrastructure.orm.models import (
    CatalogoORM, TiendaORM,
    SegmentacionSKUORM, SegmentacionTiendaORM, MarketBasketORM,
)
from app.core.exceptions import DatabaseException
from app.infrastructure.repositories.inventory_repository import _df_to_records


class ProductRepository(IProductRepository):
    """Implementación PostgreSQL para catálogos, tiendas y análisis de productos."""

    def __init__(self, db: Session):
        self._db = db

    # ── Productos ────────────────────────────────────────────────

    def get_all_products(self, limit: int = 200) -> List[Product]:
        try:
            rows = self._db.query(CatalogoORM).limit(limit).all()
            return [self._cat_to_entity(r) for r in rows]
        except SQLAlchemyError as e:
            raise DatabaseException(detail=str(e))

    def get_product_by_sku(self, sku_id: str) -> Optional[Product]:
        """sku_id = id::VARCHAR según el esquema real de la BD."""
        try:
            try:
                pk = int(sku_id)
            except (ValueError, TypeError):
                return None
            row = self._db.query(CatalogoORM).filter(CatalogoORM.id == pk).first()
            return self._cat_to_entity(row) if row else None
        except SQLAlchemyError as e:
            raise DatabaseException(detail=str(e))

    def _cat_to_entity(self, r: CatalogoORM) -> Product:
        return Product(
            id=r.id,
            sku_id=str(r.id),                    # sku_id = id::VARCHAR
            nombre=r.name or "",
            categoria=r.categories or "",
            marca=r.brands or "",
            precio=r.price or 0.0,
            costo=r.cost or 0.0,
            departamento=r.department_name,
            tipolinea=r.custom_tipolinea,
            season=r.seasons,
        )

    # ── Tiendas ──────────────────────────────────────────────────

    def get_all_stores(self) -> List[Store]:
        try:
            rows = self._db.query(TiendaORM).all()
            return [self._store_to_entity(r) for r in rows]
        except SQLAlchemyError as e:
            raise DatabaseException(detail=str(e))

    def get_store_by_id(self, store_id: str) -> Optional[Store]:
        """tienda_id = id::VARCHAR según el esquema real de la BD."""
        try:
            try:
                pk = int(store_id)
            except (ValueError, TypeError):
                return None
            row = self._db.query(TiendaORM).filter(TiendaORM.id == pk).first()
            return self._store_to_entity(row) if row else None
        except SQLAlchemyError as e:
            raise DatabaseException(detail=str(e))

    def _store_to_entity(self, r: TiendaORM) -> Store:
        return Store(
            id=r.id,
            tienda_id=str(r.id),                 # tienda_id = id::VARCHAR
            nombre=r.name or "",
            ciudad=r.city or "",
            region=r.region or "",
            formato=r.custom_formato,
            clima=r.custom_clima,
            zona=r.custom_zona,
        )

    # ── Segmentación ─────────────────────────────────────────────

    def get_segmentation(self, segment: Optional[str] = None) -> pd.DataFrame:
        try:
            q = self._db.query(SegmentacionSKUORM)
            if segment:
                q = q.filter(SegmentacionSKUORM.segmento_abc == segment.upper())
            rows = q.order_by(SegmentacionSKUORM.acumulado).all()
            if not rows:
                return pd.DataFrame()
            return pd.DataFrame([{
                "sku_id": r.sku_id,
                "participacion": r.participacion,
                "acumulado": r.acumulado,
                "segmento_abc": r.segmento_abc,
            } for r in rows])
        except SQLAlchemyError as e:
            raise DatabaseException(detail=str(e))

    def get_store_segmentation(self) -> pd.DataFrame:
        try:
            rows = self._db.query(SegmentacionTiendaORM).all()
            if not rows:
                return pd.DataFrame()
            return pd.DataFrame([{
                "tienda_id": r.tienda_id,
                "ventas_totales": r.ventas_totales,
                "venta_promedio": r.venta_promedio,
                "num_skus": r.num_skus,
                "segmento_tienda": r.segmento_tienda,
            } for r in rows])
        except SQLAlchemyError as e:
            raise DatabaseException(detail=str(e))

    # ── Market Basket ────────────────────────────────────────────

    def get_market_basket(self, min_lift: float = 1.0) -> pd.DataFrame:
        try:
            rows = (
                self._db.query(MarketBasketORM)
                .filter(MarketBasketORM.lift >= min_lift)
                .order_by(MarketBasketORM.lift.desc())
                .all()
            )
            if not rows:
                return pd.DataFrame()
            return pd.DataFrame([{
                "sku_origen": r.sku_origen,
                "sku_destino": r.sku_destino,
                "soporte": r.soporte,
                "confianza": r.confianza,
                "lift": r.lift,
                "conviction": r.conviction,
            } for r in rows])
        except SQLAlchemyError as e:
            raise DatabaseException(detail=str(e))

    # ── Persistencia ─────────────────────────────────────────────

    def save_segmentation(self, df: pd.DataFrame) -> int:
        try:
            self._db.query(SegmentacionSKUORM).delete()
            self._db.bulk_insert_mappings(SegmentacionSKUORM, _df_to_records(df))
            self._db.commit()
            return len(df)
        except SQLAlchemyError as e:
            self._db.rollback()
            raise DatabaseException(message=f"save_segmentation: {e.__class__.__name__}: {e}", detail=str(e))

    def save_market_basket(self, df: pd.DataFrame) -> int:
        try:
            self._db.query(MarketBasketORM).delete()
            self._db.bulk_insert_mappings(MarketBasketORM, _df_to_records(df))
            self._db.commit()
            return len(df)
        except SQLAlchemyError as e:
            self._db.rollback()
            raise DatabaseException(message=f"save_market_basket: {e.__class__.__name__}: {e}", detail=str(e))
