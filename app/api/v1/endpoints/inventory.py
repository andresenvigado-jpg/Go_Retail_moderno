from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.config.database import get_db, engine
from app.core.dependencies import get_current_user, require_analyst
from app.infrastructure.repositories.inventory_repository import InventoryRepository
from app.application.use_cases.inventory_use_cases import (
    GetAnomaliesUseCase, GetEOQUseCase, GetMonteCarloUseCase,
    RunAnomalyModelUseCase, RunEOQModelUseCase, RunMonteCarloModelUseCase,
)
from app.application.dtos.inventory_dto import (
    AnomalyResponse, EOQResponse, MonteCarloResponse,
)
from app.application.dtos.demand_dto import RunModelResponse

router = APIRouter(prefix="/inventory", tags=["Inventario & Riesgo"])

ANOMALY_TYPES = ["🔴 Quiebre de stock", "🟠 Riesgo de quiebre", "🟡 Sobrestock", "🔵 Sin movimiento"]


@router.get(
    "/anomalies",
    response_model=AnomalyResponse,
    summary="Anomalías de inventario",
    description="Retorna alertas detectadas por Isolation Forest. Filtrable por tipo de anomalía.",
)
def get_anomalies(
    tipo: Optional[str] = Query(None, description=f"Tipo de anomalía: {ANOMALY_TYPES}"),
    limit: int = Query(100, ge=1, le=2000),
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    return GetAnomaliesUseCase(InventoryRepository(db)).execute(tipo=tipo, limit=limit)


@router.get(
    "/eoq",
    response_model=EOQResponse,
    summary="Resultados EOQ",
    description="Cantidad óptima de pedido por SKU-Tienda. Filtrable por SKU y/o tienda.",
)
def get_eoq(
    sku_id: Optional[str] = Query(None),
    store_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    return GetEOQUseCase(InventoryRepository(db)).execute(sku_id=sku_id, store_id=store_id)


@router.get(
    "/eoq/{sku_id}/{store_id}",
    response_model=EOQResponse,
    summary="EOQ por SKU y Tienda",
)
def get_eoq_by_sku_store(
    sku_id: str,
    store_id: str,
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    return GetEOQUseCase(InventoryRepository(db)).execute(sku_id=sku_id, store_id=store_id)


@router.get(
    "/monte-carlo",
    response_model=MonteCarloResponse,
    summary="Simulación Monte Carlo",
    description="Probabilidad de quiebre de stock por SKU-Tienda con 1,000 escenarios.",
)
def get_monte_carlo(
    sku_id: Optional[str] = Query(None),
    store_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    return GetMonteCarloUseCase(InventoryRepository(db)).execute(
        sku_id=sku_id, store_id=store_id
    )


@router.get(
    "/monte-carlo/{sku_id}/{store_id}",
    response_model=MonteCarloResponse,
    summary="Monte Carlo por SKU y Tienda",
)
def get_monte_carlo_by_sku_store(
    sku_id: str,
    store_id: str,
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    return GetMonteCarloUseCase(InventoryRepository(db)).execute(
        sku_id=sku_id, store_id=store_id
    )


@router.post(
    "/run/anomalies",
    response_model=RunModelResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Ejecutar detección de anomalías",
    dependencies=[Depends(require_analyst)],
)
def run_anomalies(db: Session = Depends(get_db)):
    return RunAnomalyModelUseCase(InventoryRepository(db), engine).execute()


@router.post(
    "/run/eoq",
    response_model=RunModelResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Ejecutar cálculo EOQ",
    dependencies=[Depends(require_analyst)],
)
def run_eoq(db: Session = Depends(get_db)):
    return RunEOQModelUseCase(InventoryRepository(db), engine).execute()


@router.post(
    "/run/monte-carlo",
    response_model=RunModelResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Ejecutar simulación Monte Carlo",
    dependencies=[Depends(require_analyst)],
)
def run_monte_carlo(db: Session = Depends(get_db)):
    return RunMonteCarloModelUseCase(InventoryRepository(db), engine).execute()
