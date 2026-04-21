from typing import Optional
from sqlalchemy.engine import Engine

from app.domain.interfaces.i_inventory_repository import IInventoryRepository
from app.core.exceptions import MLModelException, GoRetailException
from app.application.dtos.inventory_dto import (
    AnomalyResponse, AnomalyItem,
    EOQResponse, EOQItem,
    MonteCarloResponse, MonteCarloItem,
)
from app.application.dtos.demand_dto import RunModelResponse


class GetAnomaliesUseCase:
    def __init__(self, repo: IInventoryRepository):
        self._repo = repo

    def execute(self, tipo: Optional[str] = None, limit: int = 100) -> AnomalyResponse:
        df = self._repo.get_anomalies(tipo=tipo, limit=limit)
        if df.empty:
            return AnomalyResponse(total=0, criticas=0, data=[])
        items = [AnomalyItem(**row) for row in df.to_dict(orient="records")]
        criticas = sum(1 for i in items if "quiebre" in i.tipo_anomalia.lower())
        return AnomalyResponse(total=len(items), criticas=criticas, data=items)


class GetEOQUseCase:
    def __init__(self, repo: IInventoryRepository):
        self._repo = repo

    def execute(self, sku_id: Optional[str] = None, store_id: Optional[str] = None) -> EOQResponse:
        df = self._repo.get_eoq(sku_id=sku_id, store_id=store_id)
        if df.empty:
            return EOQResponse(total=0, data=[])
        items = [EOQItem(**row) for row in df.to_dict(orient="records")]
        return EOQResponse(total=len(items), data=items)


class GetMonteCarloUseCase:
    def __init__(self, repo: IInventoryRepository):
        self._repo = repo

    def execute(
        self, sku_id: Optional[str] = None, store_id: Optional[str] = None
    ) -> MonteCarloResponse:
        df = self._repo.get_monte_carlo(sku_id=sku_id, store_id=store_id)
        if df.empty:
            return MonteCarloResponse(total=0, alto_riesgo=0, data=[])
        items = [MonteCarloItem(**row) for row in df.to_dict(orient="records")]
        alto_riesgo = sum(1 for i in items if i.prob_quiebre >= 0.40)
        return MonteCarloResponse(total=len(items), alto_riesgo=alto_riesgo, data=items)


class RunAnomalyModelUseCase:
    def __init__(self, repo: IInventoryRepository, engine: Engine):
        self._repo = repo
        self._engine = engine

    def execute(self) -> RunModelResponse:
        try:
            from app.infrastructure.ml.modelo_anomalias import ejecutar_anomalias
            df = ejecutar_anomalias(self._engine)
            saved = self._repo.save_anomalies(df)
            return RunModelResponse(
                model="IsolationForest",
                status="success",
                records_saved=saved,
                message=f"Anomalías detectadas: {df['es_anomalia'].sum()} de {saved}",
            )
        except GoRetailException:
            raise
        except Exception as e:
            raise MLModelException("IsolationForest", detail=repr(e))


class RunEOQModelUseCase:
    def __init__(self, repo: IInventoryRepository, engine: Engine):
        self._repo = repo
        self._engine = engine

    def execute(self) -> RunModelResponse:
        try:
            from app.infrastructure.ml.modelo_eoq import ejecutar_eoq
            df = ejecutar_eoq(self._engine)
            saved = self._repo.save_eoq(df)
            return RunModelResponse(
                model="EOQ",
                status="success",
                records_saved=saved,
                message=f"Cálculo EOQ completado para {saved} combinaciones SKU-Tienda",
            )
        except GoRetailException:
            raise
        except Exception as e:
            raise MLModelException("EOQ", detail=repr(e))


class RunMonteCarloModelUseCase:
    def __init__(self, repo: IInventoryRepository, engine: Engine):
        self._repo = repo
        self._engine = engine

    def execute(self) -> RunModelResponse:
        try:
            from app.infrastructure.ml.modelo_monte_carlo import ejecutar_monte_carlo
            df = ejecutar_monte_carlo(self._engine)
            saved = self._repo.save_monte_carlo(df)
            return RunModelResponse(
                model="MonteCarlo",
                status="success",
                records_saved=saved,
                message=f"Simulación completada: {saved} combinaciones SKU-Tienda",
            )
        except Exception as e:
            raise MLModelException("MonteCarlo", detail=str(e))
