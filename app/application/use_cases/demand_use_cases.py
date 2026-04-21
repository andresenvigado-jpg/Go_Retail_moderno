from typing import Optional
from sqlalchemy.engine import Engine

from app.domain.interfaces.i_demand_repository import IDemandRepository
from app.core.exceptions import NotFoundException, MLModelException
from app.application.dtos.demand_dto import (
    ForecastResponse, ForecastItem,
    LGBMPredictionResponse, LGBMPredictionItem,
    RunModelResponse,
)


class GetForecastsUseCase:
    """Retorna pronósticos Prophet almacenados."""

    def __init__(self, repo: IDemandRepository):
        self._repo = repo

    def execute(self, sku_id: Optional[str] = None, limit: int = 100) -> ForecastResponse:
        df = self._repo.get_forecasts(sku_id=sku_id, limit=limit)
        if df.empty:
            return ForecastResponse(total=0, data=[])
        items = [ForecastItem(**row) for row in df.to_dict(orient="records")]
        return ForecastResponse(total=len(items), data=items)


class GetLGBMPredictionsUseCase:
    """Retorna predicciones LightGBM almacenadas."""

    def __init__(self, repo: IDemandRepository):
        self._repo = repo

    def execute(
        self,
        sku_id: Optional[str] = None,
        store_id: Optional[str] = None,
        limit: int = 100,
    ) -> LGBMPredictionResponse:
        df = self._repo.get_lgbm_predictions(sku_id=sku_id, store_id=store_id, limit=limit)
        if df.empty:
            return LGBMPredictionResponse(total=0, mae=None, data=[])

        mae = None
        if "cantidad_real" in df.columns:
            valid = df.dropna(subset=["cantidad_real"])
            if not valid.empty:
                mae = round(
                    abs(valid["cantidad_real"] - valid["cantidad_predicha"]).mean(), 4
                )

        items = [LGBMPredictionItem(**row) for row in df.to_dict(orient="records")]
        return LGBMPredictionResponse(total=len(items), mae=mae, data=items)


class RunProphetModelUseCase:
    """Ejecuta el modelo Prophet y persiste resultados."""

    def __init__(self, repo: IDemandRepository, engine: Engine):
        self._repo = repo
        self._engine = engine

    def execute(self) -> RunModelResponse:
        try:
            from app.infrastructure.ml.modelo_pronostico import ejecutar_pronostico
            df = ejecutar_pronostico(self._engine)
            saved = self._repo.save_forecasts(df)
            return RunModelResponse(
                model="Prophet",
                status="success",
                records_saved=saved,
                message=f"Pronóstico generado para {df['sku_id'].nunique()} SKUs",
            )
        except Exception as e:
            raise MLModelException("Prophet", detail=str(e))


class RunLGBMModelUseCase:
    """Ejecuta el modelo LightGBM y persiste resultados."""

    def __init__(self, repo: IDemandRepository, engine: Engine):
        self._repo = repo
        self._engine = engine

    def execute(self) -> RunModelResponse:
        try:
            from app.infrastructure.ml.modelo_lightgbm import ejecutar_lightgbm
            df = ejecutar_lightgbm(self._engine)
            saved = self._repo.save_lgbm_predictions(df)
            return RunModelResponse(
                model="LightGBM",
                status="success",
                records_saved=saved,
                message=f"Predicciones generadas: {saved} registros",
            )
        except Exception as e:
            raise MLModelException("LightGBM", detail=str(e))
