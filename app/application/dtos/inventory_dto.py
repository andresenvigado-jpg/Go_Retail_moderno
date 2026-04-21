from typing import List, Optional
from pydantic import BaseModel


class AnomalyItem(BaseModel):
    sku_id: str
    tienda_id: str
    tipo_anomalia: str
    es_anomalia: bool
    score_anomalia: float
    stock_actual: Optional[float]
    cobertura_dias: Optional[float]

    model_config = {"from_attributes": True}


class AnomalyResponse(BaseModel):
    total: int
    criticas: int
    data: List[AnomalyItem]


class EOQItem(BaseModel):
    sku_id: str
    tienda_id: str
    eoq: float
    punto_reorden: float
    stock_seguridad: float
    estado_reposicion: str
    dias_entre_pedidos: Optional[float]
    costo_total_anual: Optional[float]

    model_config = {"from_attributes": True}


class EOQResponse(BaseModel):
    total: int
    data: List[EOQItem]


class MonteCarloItem(BaseModel):
    sku_id: str
    tienda_id: str
    demanda_p50: float
    demanda_p90: float
    demanda_p95: float
    demanda_p99: float
    prob_quiebre: float
    stock_recomendado: float
    nivel_riesgo: str

    model_config = {"from_attributes": True}


class MonteCarloResponse(BaseModel):
    total: int
    alto_riesgo: int
    data: List[MonteCarloItem]
