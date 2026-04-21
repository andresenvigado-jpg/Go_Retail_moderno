from typing import List, Optional
from pydantic import BaseModel


class RentabilityItem(BaseModel):
    sku_id: str
    tienda_id: Optional[str] = None
    margen_porcentual: Optional[float] = None
    rentabilidad_total: Optional[float] = None
    indice_rentabilidad: Optional[float] = None
    clasificacion: Optional[str] = None

    model_config = {"from_attributes": True}


class RentabilityResponse(BaseModel):
    total: int
    promedio_margen: float
    data: List[RentabilityItem]


class RotationItem(BaseModel):
    sku_id: str
    tienda_id: Optional[str] = None
    tasa_rotacion_anual: Optional[float] = None
    dsi: Optional[float] = None
    frecuencia_venta: Optional[float] = None
    indice_velocidad: Optional[float] = None
    clasificacion: Optional[str] = None

    model_config = {"from_attributes": True}


class RotationResponse(BaseModel):
    total: int
    data: List[RotationItem]


class EfficiencyItem(BaseModel):
    tienda_id: str
    cobertura_reposicion: Optional[float] = None
    tasa_devolucion: Optional[float] = None
    eficiencia_skus: Optional[float] = None
    indice_eficiencia: Optional[float] = None
    clasificacion: Optional[str] = None

    model_config = {"from_attributes": True}


class EfficiencyResponse(BaseModel):
    total: int
    promedio_eficiencia: float
    data: List[EfficiencyItem]
