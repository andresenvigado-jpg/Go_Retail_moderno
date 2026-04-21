from abc import ABC, abstractmethod
from typing import List, Optional
import pandas as pd


class IDemandRepository(ABC):
    """Contrato para acceso a datos de demanda y pronósticos."""

    @abstractmethod
    def get_forecasts(self, sku_id: Optional[str] = None, limit: int = 100) -> pd.DataFrame:
        ...

    @abstractmethod
    def get_lgbm_predictions(
        self,
        sku_id: Optional[str] = None,
        store_id: Optional[str] = None,
        limit: int = 100,
    ) -> pd.DataFrame:
        ...

    @abstractmethod
    def save_forecasts(self, df: pd.DataFrame) -> int:
        """Persiste pronósticos. Retorna cantidad de registros guardados."""
        ...

    @abstractmethod
    def save_lgbm_predictions(self, df: pd.DataFrame) -> int:
        ...
