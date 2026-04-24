from fastapi import APIRouter
from app.api.v1.endpoints import auth, demand, inventory, analytics, products, stores, admin, compliance

api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(demand.router)
api_router.include_router(inventory.router)
api_router.include_router(analytics.router)
api_router.include_router(products.router)
api_router.include_router(stores.router)
api_router.include_router(admin.router)
api_router.include_router(compliance.router)
