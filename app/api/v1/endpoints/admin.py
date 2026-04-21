from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.config.database import get_db, engine
from app.core.dependencies import require_admin, require_analyst
from app.application.dtos.demand_dto import RunModelResponse
from app.infrastructure.repositories.demand_repository import DemandRepository
from app.infrastructure.repositories.inventory_repository import InventoryRepository
from app.infrastructure.repositories.analytics_repository import AnalyticsRepository
from app.infrastructure.repositories.product_repository import ProductRepository
from app.application.use_cases.demand_use_cases import RunProphetModelUseCase, RunLGBMModelUseCase
from app.application.use_cases.inventory_use_cases import (
    RunAnomalyModelUseCase, RunEOQModelUseCase, RunMonteCarloModelUseCase,
)
from app.application.use_cases.analytics_use_cases import (
    RunRentabilityModelUseCase, RunRotationModelUseCase, RunEfficiencyModelUseCase,
)
from app.application.use_cases.product_use_cases import (
    RunSegmentationModelUseCase, RunMarketBasketModelUseCase,
)

router = APIRouter(prefix="/admin", tags=["Administración"])


@router.post(
    "/run-all-models",
    summary="Ejecutar todos los modelos ML",
    description=(
        "Ejecuta los 10 modelos ML en secuencia y retorna el resultado de cada uno. "
        "Solo admins. Puede tardar varios minutos."
    ),
    dependencies=[Depends(require_admin)],
)
def run_all_models(db: Session = Depends(get_db)):
    results = []
    jobs = [
        ("Prophet",            RunProphetModelUseCase(DemandRepository(db), engine)),
        ("LightGBM",           RunLGBMModelUseCase(DemandRepository(db), engine)),
        ("Anomalías",          RunAnomalyModelUseCase(InventoryRepository(db), engine)),
        ("EOQ",                RunEOQModelUseCase(InventoryRepository(db), engine)),
        ("MonteCarlo",         RunMonteCarloModelUseCase(InventoryRepository(db), engine)),
        ("Rentabilidad",       RunRentabilityModelUseCase(AnalyticsRepository(db), engine)),
        ("Rotación",           RunRotationModelUseCase(AnalyticsRepository(db), engine)),
        ("Eficiencia",         RunEfficiencyModelUseCase(AnalyticsRepository(db), engine)),
        ("Segmentación",       RunSegmentationModelUseCase(ProductRepository(db), engine)),
        ("MarketBasket",       RunMarketBasketModelUseCase(ProductRepository(db), engine)),
    ]
    for name, use_case in jobs:
        try:
            result = use_case.execute()
            results.append(result.model_dump())
        except Exception as exc:
            results.append({
                "model": name,
                "status": "error",
                "records_saved": 0,
                "message": str(exc),
            })
    return {"total_models": len(jobs), "results": results}


@router.post(
    "/load-incremental",
    summary="Carga incremental de datos",
    description="Ejecuta el script de carga incremental para agregar nuevas transacciones.",
    dependencies=[Depends(require_analyst)],
)
def load_incremental():
    try:
        import subprocess
        import sys
        result = subprocess.run(
            [sys.executable, "scripts/carga_incremental.py"],
            capture_output=True, text=True, timeout=120,
        )
        return {
            "status": "ok" if result.returncode == 0 else "error",
            "output": result.stdout[-2000:] if result.stdout else "",
            "error": result.stderr[-1000:] if result.stderr else "",
        }
    except Exception as exc:
        return {"status": "error", "message": str(exc)}
