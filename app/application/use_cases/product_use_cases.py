from typing import List, Optional
from sqlalchemy.engine import Engine

from app.domain.interfaces.i_product_repository import IProductRepository
from app.core.exceptions import NotFoundException, MLModelException
from app.application.dtos.product_dto import (
    ProductResponse, StoreResponse,
    SegmentationResponse, SegmentationItem,
    MarketBasketResponse, MarketBasketItem,
    StoreSegmentationItem,
)
from app.application.dtos.demand_dto import RunModelResponse


class GetProductsUseCase:
    def __init__(self, repo: IProductRepository):
        self._repo = repo

    def execute(self, limit: int = 200) -> List[ProductResponse]:
        products = self._repo.get_all_products(limit=limit)
        return [
            ProductResponse(
                sku_id=p.sku_id,
                nombre=p.nombre,
                categoria=p.categoria,
                marca=p.marca,
                precio=p.precio,
                costo=p.costo,
                margen_porcentual=round(p.margen_porcentual, 2),
                departamento=p.departamento,
                tipolinea=p.tipolinea,
                season=p.season,
            )
            for p in products
        ]


class GetProductBySkuUseCase:
    def __init__(self, repo: IProductRepository):
        self._repo = repo

    def execute(self, sku_id: str) -> ProductResponse:
        product = self._repo.get_product_by_sku(sku_id)
        if not product:
            raise NotFoundException("Producto", sku_id)
        return ProductResponse(
            sku_id=product.sku_id,
            nombre=product.nombre,
            categoria=product.categoria,
            marca=product.marca,
            precio=product.precio,
            costo=product.costo,
            margen_porcentual=round(product.margen_porcentual, 2),
            departamento=product.departamento,
            tipolinea=product.tipolinea,
            season=product.season,
        )


class GetStoresUseCase:
    def __init__(self, repo: IProductRepository):
        self._repo = repo

    def execute(self) -> List[StoreResponse]:
        stores = self._repo.get_all_stores()
        return [
            StoreResponse(
                tienda_id=s.tienda_id,
                nombre=s.nombre,
                ciudad=s.ciudad,
                region=s.region,
                formato=s.formato,
                clima=s.clima,
                zona=s.zona,
            )
            for s in stores
        ]


class GetStoreByIdUseCase:
    def __init__(self, repo: IProductRepository):
        self._repo = repo

    def execute(self, store_id: str) -> StoreResponse:
        store = self._repo.get_store_by_id(store_id)
        if not store:
            raise NotFoundException("Tienda", store_id)
        return StoreResponse(
            tienda_id=store.tienda_id,
            nombre=store.nombre,
            ciudad=store.ciudad,
            region=store.region,
            formato=store.formato,
            clima=store.clima,
            zona=store.zona,
        )


class GetSegmentationUseCase:
    def __init__(self, repo: IProductRepository):
        self._repo = repo

    def execute(self, segment: Optional[str] = None) -> SegmentationResponse:
        df = self._repo.get_segmentation(segment=segment)
        if df.empty:
            return SegmentationResponse(total=0, segmento_a=0, segmento_b=0, segmento_c=0, data=[])
        items = [SegmentationItem(**row) for row in df.to_dict(orient="records")]
        return SegmentationResponse(
            total=len(items),
            segmento_a=sum(1 for i in items if i.segmento_abc == "A"),
            segmento_b=sum(1 for i in items if i.segmento_abc == "B"),
            segmento_c=sum(1 for i in items if i.segmento_abc == "C"),
            data=items,
        )


class GetMarketBasketUseCase:
    def __init__(self, repo: IProductRepository):
        self._repo = repo

    def execute(self, min_lift: float = 1.0) -> MarketBasketResponse:
        df = self._repo.get_market_basket(min_lift=min_lift)
        if df.empty:
            return MarketBasketResponse(total=0, data=[])
        items = [MarketBasketItem(**row) for row in df.to_dict(orient="records")]
        return MarketBasketResponse(total=len(items), data=items)


class RunSegmentationModelUseCase:
    def __init__(self, repo: IProductRepository, engine: Engine):
        self._repo = repo
        self._engine = engine

    def execute(self) -> RunModelResponse:
        try:
            from app.infrastructure.ml.modelo_segmentacion import ejecutar_segmentacion
            df_skus, df_tiendas = ejecutar_segmentacion(self._engine)
            saved_skus = self._repo.save_segmentation(df_skus)
            return RunModelResponse(
                model="Segmentacion",
                status="success",
                records_saved=saved_skus,
                message=f"Segmentación ABC: {saved_skus} SKUs clasificados",
            )
        except Exception as e:
            raise MLModelException("Segmentacion", detail=str(e))


class RunMarketBasketModelUseCase:
    def __init__(self, repo: IProductRepository, engine: Engine):
        self._repo = repo
        self._engine = engine

    def execute(self) -> RunModelResponse:
        try:
            from app.infrastructure.ml.modelo_market_basket import ejecutar_market_basket
            df = ejecutar_market_basket(self._engine)
            saved = self._repo.save_market_basket(df)
            return RunModelResponse(
                model="MarketBasket",
                status="success",
                records_saved=saved,
                message=f"Reglas de asociación generadas: {saved}",
            )
        except Exception as e:
            raise MLModelException("MarketBasket", detail=str(e))
