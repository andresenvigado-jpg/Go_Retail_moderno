from typing import Optional
from sqlalchemy.engine import Engine

from app.domain.interfaces.i_analytics_repository import IAnalyticsRepository
from app.core.exceptions import MLModelException, GoRetailException
from app.application.dtos.analytics_dto import (
    RentabilityResponse, RentabilityItem,
    RotationResponse, RotationItem,
    EfficiencyResponse, EfficiencyItem,
)
from app.application.dtos.demand_dto import RunModelResponse


class GetRentabilityUseCase:
    def __init__(self, repo: IAnalyticsRepository):
        self._repo = repo

    def execute(self, sku_id: Optional[str] = None, limit: int = 100) -> RentabilityResponse:
        df = self._repo.get_rentability(sku_id=sku_id, limit=limit)
        if df.empty:
            return RentabilityResponse(total=0, promedio_margen=0.0, data=[])
        items = [RentabilityItem(**row) for row in df.to_dict(orient="records")]
        avg_margin = round(df["margen_porcentual"].mean(), 2)
        return RentabilityResponse(total=len(items), promedio_margen=avg_margin, data=items)


class GetRotationUseCase:
    def __init__(self, repo: IAnalyticsRepository):
        self._repo = repo

    def execute(self, sku_id: Optional[str] = None, limit: int = 100) -> RotationResponse:
        df = self._repo.get_rotation(sku_id=sku_id, limit=limit)
        if df.empty:
            return RotationResponse(total=0, data=[])
        items = [RotationItem(**row) for row in df.to_dict(orient="records")]
        return RotationResponse(total=len(items), data=items)


class GetEfficiencyUseCase:
    def __init__(self, repo: IAnalyticsRepository):
        self._repo = repo

    def execute(self, store_id: Optional[str] = None) -> EfficiencyResponse:
        df = self._repo.get_efficiency(store_id=store_id)
        if df.empty:
            return EfficiencyResponse(total=0, promedio_eficiencia=0.0, data=[])
        items = [EfficiencyItem(**row) for row in df.to_dict(orient="records")]
        avg_eff = round(df["indice_eficiencia"].mean(), 2)
        return EfficiencyResponse(total=len(items), promedio_eficiencia=avg_eff, data=items)


class RunRentabilityModelUseCase:
    def __init__(self, repo: IAnalyticsRepository, engine: Engine):
        self._repo = repo
        self._engine = engine

    def execute(self) -> RunModelResponse:
        try:
            from app.infrastructure.ml.modelo_rentabilidad import ejecutar_rentabilidad
            df = ejecutar_rentabilidad(self._engine)
            saved = self._repo.save_rentability(df)
            return RunModelResponse(
                model="Rentabilidad",
                status="success",
                records_saved=saved,
                message=f"Análisis de rentabilidad para {saved} SKUs completado",
            )
        except GoRetailException:
            raise
        except Exception as e:
            raise MLModelException("Rentabilidad", detail=repr(e))


class RunRotationModelUseCase:
    def __init__(self, repo: IAnalyticsRepository, engine: Engine):
        self._repo = repo
        self._engine = engine

    def execute(self) -> RunModelResponse:
        try:
            from app.infrastructure.ml.modelo_rotacion import ejecutar_rotacion
            df = ejecutar_rotacion(self._engine)
            saved = self._repo.save_rotation(df)
            return RunModelResponse(
                model="Rotación",
                status="success",
                records_saved=saved,
                message=f"Análisis de rotación para {saved} SKUs completado",
            )
        except GoRetailException:
            raise
        except Exception as e:
            raise MLModelException("Rotación", detail=repr(e))


class RunEfficiencyModelUseCase:
    def __init__(self, repo: IAnalyticsRepository, engine: Engine):
        self._repo = repo
        self._engine = engine

    def execute(self) -> RunModelResponse:
        try:
            from app.infrastructure.ml.modelo_eficiencia_reposicion import ejecutar_eficiencia
            df = ejecutar_eficiencia(self._engine)
            saved = self._repo.save_efficiency(df)
            return RunModelResponse(
                model="EficienciaReposicion",
                status="success",
                records_saved=saved,
                message=f"Eficiencia calculada para {saved} tiendas",
            )
        except GoRetailException:
            raise
        except Exception as e:
            raise MLModelException("EficienciaReposicion", detail=repr(e))
