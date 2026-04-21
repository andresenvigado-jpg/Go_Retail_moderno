from dataclasses import dataclass
from typing import Optional


@dataclass
class Inventory:
    """Entidad de dominio Inventario."""
    sku_id: str
    tienda_id: str
    stock_actual: float
    stock_transito: float = 0.0
    stock_reservado: float = 0.0
    stock_minimo: float = 0.0
    stock_maximo: float = 0.0
    lead_time: int = 7
    id: Optional[int] = None

    @property
    def stock_disponible(self) -> float:
        return self.stock_actual - self.stock_reservado

    @property
    def necesita_reposicion(self) -> bool:
        return self.stock_disponible <= self.stock_minimo
