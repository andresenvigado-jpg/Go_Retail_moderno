from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import random

from app.config.database import get_db, engine
from app.core.dependencies import require_admin, require_analyst, get_current_user
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


@router.post(
    "/check-and-load",
    summary="Validar y cargar datos del día",
    description="Verifica si hay datos del día actual. Si no, genera transacciones sintéticas automáticamente.",
    dependencies=[Depends(get_current_user)],
)
def check_and_load(db: Session = Depends(get_db)):
    try:
        TEMPORADA_ALTA = [1, 2, 6, 7, 10, 11, 12]
        TIPO_TRANSAC   = ["venta", "reposicion", "devolucion", "traslado"]

        # 1. Verificar última fecha con datos
        result = db.execute(
            __import__("sqlalchemy").text("SELECT MAX(transaction_date) FROM transacciones")
        ).fetchone()
        ultima_fecha = result[0] if result and result[0] else datetime.now() - timedelta(days=3)

        dias_pendientes = (datetime.now() - ultima_fecha).days
        if dias_pendientes <= 0:
            return {"status": "ok", "message": "Datos al día", "transacciones_nuevas": 0}

        # 2. Obtener tiendas y SKUs
        tiendas = [str(r[0]) for r in db.execute(
            __import__("sqlalchemy").text("SELECT id FROM tiendas")
        ).fetchall()]
        skus = [str(r[0]) for r in db.execute(
            __import__("sqlalchemy").text("SELECT id FROM catalogos")
        ).fetchall()]

        if not tiendas or not skus:
            return {"status": "error", "message": "No hay tiendas o SKUs en la base de datos"}

        # 3. Generar transacciones faltantes
        total = 0
        fecha = ultima_fecha + timedelta(days=1)
        fecha_hasta = datetime.now()

        while fecha <= fecha_hasta:
            mes = fecha.month
            ventas_dia = random.randint(15, 30) if mes in TEMPORADA_ALTA else random.randint(5, 15)

            for _ in range(ventas_dia):
                tienda_id = random.choice(tiendas)
                sku_id    = random.choice(skus)
                tipo      = random.choices(TIPO_TRANSAC, weights=[70, 15, 10, 5])[0]
                cantidad  = random.randint(1, 5) if tipo == "venta" else random.randint(5, 30)
                precio    = round(random.uniform(30000, 350000), 2) if tipo == "venta" else 0

                db.execute(__import__("sqlalchemy").text("""
                    INSERT INTO transacciones
                        (receipt_id, sku_id, source_location_id, target_location_id,
                         quantity, sale_price, currency, type,
                         transaction_date, transaction_date_process)
                    VALUES
                        (:receipt_id, :sku_id, :source, :target,
                         :qty, :price, 'COP', :tipo,
                         :fecha, :now)
                """), {
                    "receipt_id": f"AUTO_{total:08d}",
                    "sku_id":     sku_id,
                    "source":     "BODEGA_CENTRAL",
                    "target":     tienda_id,
                    "qty":        cantidad,
                    "price":      precio,
                    "tipo":       tipo,
                    "fecha":      fecha,
                    "now":        datetime.now(),
                })
                total += 1

            fecha += timedelta(days=1)

        db.commit()

        return {
            "status":               "ok",
            "message":              f"Datos generados correctamente",
            "dias_cargados":        dias_pendientes,
            "transacciones_nuevas": total,
        }

    except Exception as exc:
        db.rollback()
        return {"status": "error", "message": str(exc)}
