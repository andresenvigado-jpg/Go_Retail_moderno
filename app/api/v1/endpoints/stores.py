from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.core.dependencies import get_current_user
from app.infrastructure.repositories.product_repository import ProductRepository
from app.application.use_cases.product_use_cases import (
    GetStoresUseCase, GetStoreByIdUseCase, GetSegmentationUseCase,
)
from app.application.dtos.product_dto import StoreResponse, StoreSegmentationItem

router = APIRouter(prefix="/stores", tags=["Tiendas"])


@router.get(
    "",
    response_model=List[StoreResponse],
    summary="Lista de tiendas",
    description="Retorna todas las tiendas con sus características (formato, clima, zona).",
)
def get_stores(
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    return GetStoresUseCase(ProductRepository(db)).execute()


@router.get(
    "/{store_id}",
    response_model=StoreResponse,
    summary="Detalle de una tienda",
)
def get_store(
    store_id: str,
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    return GetStoreByIdUseCase(ProductRepository(db)).execute(store_id)


@router.get(
    "/segmentation/clusters",
    response_model=List[StoreSegmentationItem],
    summary="Segmentación de tiendas por K-Means",
    description="Agrupa tiendas en clusters por volumen de ventas y diversidad de SKUs.",
)
def get_store_segmentation(
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    repo = ProductRepository(db)
    df = repo.get_store_segmentation()
    if df.empty:
        return []
    return [StoreSegmentationItem(**row) for row in df.to_dict(orient="records")]
