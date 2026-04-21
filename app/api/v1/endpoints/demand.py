from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.config.database import get_db, engine
from app.core.dependencies import get_current_user, require_analyst
from app.infrastructure.repositories.demand_repository import DemandRepository
from app.application.use_cases.demand_use_cases import (
    GetForecastsUseCase, GetLGBMPredictionsUseCase,
    RunProphetModelUseCase, RunLGBMModelUseCase,
)
from app.application.dtos.demand_dto import (
    ForecastResponse, LGBMPredictionResponse, RunModelResponse,
)

router = APIRouter(prefix="/demand", tags=["Demanda & Pronósticos"])


@router.get(
    "/forecasts",
    response_model=ForecastResponse,
    summary="Pronósticos Prophet",
    description="Retorna pronósticos de demanda generados con Prophet (30 días). Filtrable por SKU.",
)
def get_forecasts(
    sku_id: Optional[str] = Query(None, description="ID del SKU (ej: 42)"),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    return GetForecastsUseCase(DemandRepository(db)).execute(sku_id=sku_id, limit=limit)


@router.get(
    "/forecasts/{sku_id}",
    response_model=ForecastResponse,
    summary="Pronóstico de un SKU",
)
def get_forecast_by_sku(
    sku_id: str,
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    return GetForecastsUseCase(DemandRepository(db)).execute(sku_id=sku_id, limit=30)


@router.get(
    "/predictions",
    response_model=LGBMPredictionResponse,
    summary="Predicciones LightGBM",
    description="Retorna predicciones por SKU-Tienda del modelo LightGBM. Incluye MAE calculado.",
)
def get_predictions(
    sku_id: Optional[str] = Query(None),
    store_id: Optional[str] = Query(None, description="ID de tienda"),
    limit: int = Query(100, ge=1, le=5000),
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    return GetLGBMPredictionsUseCase(DemandRepository(db)).execute(
        sku_id=sku_id, store_id=store_id, limit=limit
    )


@router.post(
    "/run/prophet",
    response_model=RunModelResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Ejecutar modelo Prophet",
    description="Re-entrena Prophet y actualiza pronósticos. Requiere rol analyst o admin.",
    dependencies=[Depends(require_analyst)],
)
def run_prophet(db: Session = Depends(get_db)):
    return RunProphetModelUseCase(DemandRepository(db), engine).execute()


@router.post(
    "/run/lightgbm",
    response_model=RunModelResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Ejecutar modelo LightGBM",
    description="Re-entrena LightGBM y actualiza predicciones. Requiere rol analyst o admin.",
    dependencies=[Depends(require_analyst)],
)
def run_lightgbm(db: Session = Depends(get_db)):
    return RunLGBMModelUseCase(DemandRepository(db), engine).execute()
