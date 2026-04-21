from abc import ABC, abstractmethod
from typing import Optional
import pandas as pd


class IInventoryRepository(ABC):
    """Contrato para acceso a datos de inventario y modelos relacionados."""

    @abstractmethod
    def get_anomalies(self, tipo: Optional[str] = None, limit: int = 100) -> pd.DataFrame:
        ...

    @abstractmethod
    def get_eoq(self, sku_id: Optional[str] = None, store_id: Optional[str] = None) -> pd.DataFrame:
        ...

    @abstractmethod
    def get_monte_carlo(
        self, sku_id: Optional[str] = None, store_id: Optional[str] = None
    ) -> pd.DataFrame:
        ...

    @abstractmethod
    def save_anomalies(self, df: pd.DataFrame) -> int:
        ...

    @abstractmethod
    def save_eoq(self, df: pd.DataFrame) -> int:
        ...

    @abstractmethod
    def save_monte_carlo(self, df: pd.DataFrame) -> int:
        ...
