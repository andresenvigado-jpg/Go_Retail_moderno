from dataclasses import dataclass
from typing import Optional


@dataclass
class Product:
    """Entidad de dominio Producto (SKU)."""
    sku_id: str
    nombre: str
    categoria: str
    marca: str
    precio: float
    costo: float
    departamento: Optional[str] = None
    tipolinea: Optional[str] = None
    season: Optional[str] = None
    id: Optional[int] = None

    @property
    def margen(self) -> float:
        return self.precio - self.costo

    @property
    def margen_porcentual(self) -> float:
        if self.precio == 0:
            return 0.0
        return (self.margen / self.precio) * 100
