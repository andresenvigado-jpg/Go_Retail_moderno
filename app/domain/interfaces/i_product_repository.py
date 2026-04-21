from abc import ABC, abstractmethod
from typing import List, Optional
import pandas as pd
from app.domain.entities.product import Product
from app.domain.entities.store import Store


class IProductRepository(ABC):
    """Contrato para acceso a catálogos, tiendas y análisis de productos."""

    @abstractmethod
    def get_all_products(self, limit: int = 200) -> List[Product]:
        ...

    @abstractmethod
    def get_product_by_sku(self, sku_id: str) -> Optional[Product]:
        ...

    @abstractmethod
    def get_all_stores(self) -> List[Store]:
        ...

    @abstractmethod
    def get_store_by_id(self, store_id: str) -> Optional[Store]:
        ...

    @abstractmethod
    def get_segmentation(self, segment: Optional[str] = None) -> pd.DataFrame:
        ...

    @abstractmethod
    def get_store_segmentation(self) -> pd.DataFrame:
        ...

    @abstractmethod
    def get_market_basket(self, min_lift: float = 1.0) -> pd.DataFrame:
        ...

    @abstractmethod
    def save_segmentation(self, df: pd.DataFrame) -> int:
        ...

    @abstractmethod
    def save_market_basket(self, df: pd.DataFrame) -> int:
        ...
