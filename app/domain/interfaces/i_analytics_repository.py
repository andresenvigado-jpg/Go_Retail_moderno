from abc import ABC, abstractmethod
from typing import Optional
import pandas as pd


class IAnalyticsRepository(ABC):
    """Contrato para acceso a datos de analítica de negocio."""

    @abstractmethod
    def get_rentability(self, sku_id: Optional[str] = None, limit: int = 100) -> pd.DataFrame:
        ...

    @abstractmethod
    def get_rotation(self, sku_id: Optional[str] = None, limit: int = 100) -> pd.DataFrame:
        ...

    @abstractmethod
    def get_efficiency(self, store_id: Optional[str] = None) -> pd.DataFrame:
        ...

    @abstractmethod
    def save_rentability(self, df: pd.DataFrame) -> int:
        ...

    @abstractmethod
    def save_rotation(self, df: pd.DataFrame) -> int:
        ...

    @abstractmethod
    def save_efficiency(self, df: pd.DataFrame) -> int:
        ...
