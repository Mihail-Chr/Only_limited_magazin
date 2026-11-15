from fastapi import APIRouter
from . import dashboard, manual_sale, orders

router = APIRouter(prefix="/seller", tags=["seller"])
router.include_router(dashboard.router)
router.include_router(manual_sale.router)
router.include_router(orders.router)