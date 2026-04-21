from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.config.database import get_db, engine
from app.core.dependencies import get_current_user, require_analyst
from app.infrastructure.repositories.product_repository import ProductRepository
from app.application.use_cases.product_use_cases import (
    GetProductsUseCase, GetProductBySkuUseCase,
    GetSegmentationUseCase, GetMarketBasketUseCase,
    RunSegmentationModelUseCase, RunMarketBasketModelUseCase,
)
from app.application.dtos.product_dto import (
    ProductResponse, SegmentationResponse, MarketBasketResponse,
)
from app.application.dtos.demand_dto import RunModelResponse

router = APIRouter(prefix="/products", tags=["Productos & Segmentación"])


@router.get(
    "",
    response_model=List[ProductResponse],
    summary="Catálogo de productos",
    description="Lista todos los SKUs del catálogo con margen calculado.",
)
def get_products(
    limit: int = Query(200, ge=1, le=1000),
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    return GetProductsUseCase(ProductRepository(db)).execute(limit=limit)


@router.get(
    "/segmentation/abc",
    response_model=SegmentationResponse,
    summary="Segmentación ABC",
    description="Clasificación ABC: A=70% ventas, B=20%, C=10%. Filtrable por segmento.",
)
def get_segmentation(
    segment: Optional[str] = Query(None, description="A, B o C"),
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    return GetSegmentationUseCase(ProductRepository(db)).execute(segment=segment)


@router.get(
    "/market-basket/rules",
    response_model=MarketBasketResponse,
    summary="Reglas de asociación (Market Basket)",
    description="Productos comprados juntos. Lift > 2 = relación fuerte, > 3 = muy fuerte.",
)
def get_market_basket(
    min_lift: float = Query(1.0, ge=0.1, description="Lift mínimo para filtrar reglas"),
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    return GetMarketBasketUseCase(ProductRepository(db)).execute(min_lift=min_lift)


@router.post(
    "/run/segmentation",
    response_model=RunModelResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Ejecutar segmentación ABC + K-Means",
    dependencies=[Depends(require_analyst)],
)
def run_segmentation(db: Session = Depends(get_db)):
    return RunSegmentationModelUseCase(ProductRepository(db), engine).execute()


@router.post(
    "/run/market-basket",
    response_model=RunModelResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Ejecutar Market Basket Analysis",
    dependencies=[Depends(require_analyst)],
)
def run_market_basket(db: Session = Depends(get_db)):
    return RunMarketBasketModelUseCase(ProductRepository(db), engine).execute()
