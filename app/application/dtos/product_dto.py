from typing import List, Optional
from pydantic import BaseModel


class ProductResponse(BaseModel):
    sku_id: str
    nombre: Optional[str] = None
    categoria: Optional[str] = None
    marca: Optional[str] = None
    precio: Optional[float] = None
    costo: Optional[float] = None
    margen_porcentual: Optional[float] = None
    departamento: Optional[str] = None
    tipolinea: Optional[str] = None
    season: Optional[str] = None

    model_config = {"from_attributes": True}


class StoreResponse(BaseModel):
    tienda_id: str
    nombre: Optional[str] = None
    ciudad: Optional[str] = None
    region: Optional[str] = None
    formato: Optional[str] = None
    clima: Optional[str] = None
    zona: Optional[str] = None

    model_config = {"from_attributes": True}


class SegmentationItem(BaseModel):
    sku_id: str
    participacion: float
    acumulado: float
    segmento_abc: str

    model_config = {"from_attributes": True}


class SegmentationResponse(BaseModel):
    total: int
    segmento_a: int
    segmento_b: int
    segmento_c: int
    data: List[SegmentationItem]


class MarketBasketItem(BaseModel):
    sku_origen: str
    sku_destino: str
    soporte: float
    confianza: float
    lift: float
    conviction: Optional[float] = None

    model_config = {"from_attributes": True}


class MarketBasketResponse(BaseModel):
    total: int
    data: List[MarketBasketItem]


class StoreSegmentationItem(BaseModel):
    tienda_id: str
    nombre: Optional[str] = None
    ventas_totales: Optional[float] = None
    venta_promedio: Optional[float] = None
    num_skus: Optional[int] = None
    segmento_tienda: Optional[str] = None

    model_config = {"from_attributes": True}
