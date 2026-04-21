from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.config.database import get_db, engine
from app.core.dependencies import get_current_user, require_analyst
from app.infrastructure.repositories.analytics_repository import AnalyticsRepository
from app.application.use_cases.analytics_use_cases import (
    GetRentabilityUseCase, GetRotationUseCase, GetEfficiencyUseCase,
    RunRentabilityModelUseCase, RunRotationModelUseCase, RunEfficiencyModelUseCase,
)
from app.application.dtos.analytics_dto import (
    RentabilityResponse, RotationResponse, EfficiencyResponse,
)
from app.application.dtos.demand_dto import RunModelResponse

router = APIRouter(prefix="/analytics", tags=["Analítica de Negocio"])


@router.get(
    "/rentability",
    response_model=RentabilityResponse,
    summary="Rentabilidad por SKU",
    description="Índice de rentabilidad 0-100 por SKU. Clasificación: Alta ≥70, Media 40-70, Baja <40.",
)
def get_rentability(
    sku_id: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    return GetRentabilityUseCase(AnalyticsRepository(db)).execute(sku_id=sku_id, limit=limit)


@router.get(
    "/rentability/{sku_id}",
    response_model=RentabilityResponse,
    summary="Rentabilidad de un SKU",
)
def get_rentability_by_sku(
    sku_id: str,
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    return GetRentabilityUseCase(AnalyticsRepository(db)).execute(sku_id=sku_id, limit=1)


@router.get(
    "/rotation",
    response_model=RotationResponse,
    summary="Rotación de inventario",
    description="Tasa de rotación, DSI (días de stock) y velocidad por SKU.",
)
def get_rotation(
    sku_id: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    return GetRotationUseCase(AnalyticsRepository(db)).execute(sku_id=sku_id, limit=limit)


@router.get(
    "/rotation/{sku_id}",
    response_model=RotationResponse,
    summary="Rotación de un SKU",
)
def get_rotation_by_sku(
    sku_id: str,
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    return GetRotationUseCase(AnalyticsRepository(db)).execute(sku_id=sku_id, limit=1)


@router.get(
    "/efficiency",
    response_model=EfficiencyResponse,
    summary="Eficiencia de reposición por tienda",
    description="KPIs de reposición: cobertura, devolución, eficiencia SKUs. Filtrable por tienda.",
)
def get_efficiency(
    store_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    return GetEfficiencyUseCase(AnalyticsRepository(db)).execute(store_id=store_id)


@router.get(
    "/efficiency/{store_id}",
    response_model=EfficiencyResponse,
    summary="Eficiencia de una tienda",
)
def get_efficiency_by_store(
    store_id: str,
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    return GetEfficiencyUseCase(AnalyticsRepository(db)).execute(store_id=store_id)


@router.post(
    "/run/rentability",
    response_model=RunModelResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Ejecutar modelo de rentabilidad",
    dependencies=[Depends(require_analyst)],
)
def run_rentability(db: Session = Depends(get_db)):
    return RunRentabilityModelUseCase(AnalyticsRepository(db), engine).execute()


@router.post(
    "/run/rotation",
    response_model=RunModelResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Ejecutar modelo de rotación",
    dependencies=[Depends(require_analyst)],
)
def run_rotation(db: Session = Depends(get_db)):
    return RunRotationModelUseCase(AnalyticsRepository(db), engine).execute()


@router.post(
    "/run/efficiency",
    response_model=RunModelResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Ejecutar modelo de eficiencia",
    dependencies=[Depends(require_analyst)],
)
def run_efficiency(db: Session = Depends(get_db)):
    return RunEfficiencyModelUseCase(AnalyticsRepository(db), engine).execute()
