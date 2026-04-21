from datetime import date
from typing import List, Optional
from pydantic import BaseModel


class ForecastItem(BaseModel):
    sku_id: str
    fecha: date
    demanda_estimada: float
    demanda_minima: float
    demanda_maxima: float

    model_config = {"from_attributes": True}


class ForecastResponse(BaseModel):
    total: int
    data: List[ForecastItem]


class LGBMPredictionItem(BaseModel):
    sku_id: str
    tienda_id: str
    cantidad_real: Optional[float]
    cantidad_predicha: float

    model_config = {"from_attributes": True}


class LGBMPredictionResponse(BaseModel):
    total: int
    mae: Optional[float]
    data: List[LGBMPredictionItem]


class RunModelResponse(BaseModel):
    model: str
    status: str
    records_saved: int
    message: str
