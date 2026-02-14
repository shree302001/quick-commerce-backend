from fastapi import APIRouter
from app.api.v1.endpoints import users, orders, products, inventory, dlq

api_router = APIRouter()

api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(orders.router, prefix="/orders", tags=["orders"])
api_router.include_router(products.router, prefix="/products", tags=["products"])
api_router.include_router(inventory.router, prefix="/inventory", tags=["inventory"])
api_router.include_router(dlq.router, prefix="/dlq", tags=["dlq"])
