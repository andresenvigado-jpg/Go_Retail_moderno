from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.config.database import get_db, engine
from app.core.dependencies import get_current_user
from app.infrastructure.ml.modelo_cumplimiento import ejecutar_cumplimiento

router = APIRouter(prefix="/compliance", tags=["Cumplimiento de Metas"])


@router.get(
    "/report",
    summary="Informe de cumplimiento de metas por tienda",
    description=(
        "Genera el informe completo de cumplimiento usando KMeans (tiers), "
        "LinearRegression (tendencias) e IsolationForest (anomalías). "
        "Por defecto analiza el mes en curso."
    ),
)
def get_compliance_report(
    fecha_desde: Optional[date] = Query(None, description="Fecha inicio (YYYY-MM-DD)"),
    fecha_hasta: Optional[date] = Query(None, description="Fecha fin (YYYY-MM-DD)"),
    _=Depends(get_current_user),
):
    return ejecutar_cumplimiento(engine, fecha_desde, fecha_hasta)
