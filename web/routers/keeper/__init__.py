"""
keeper — пакет роутеров Кладовщика (v3.1).

Собирает подмодули в один router с prefix="/keeper".
"""
from fastapi import APIRouter

from . import (
    menu,
    inventory_list, inventory_update,
    products_list, products_price, products_delete,
    products_save, products_check_dup,
    forms_add, forms_edit, forms_copy,
)

router = APIRouter(prefix="/keeper", tags=["keeper"])

router.include_router(menu.router)
router.include_router(inventory_list.router)
router.include_router(inventory_update.router)
router.include_router(products_list.router)
router.include_router(products_price.router)
router.include_router(products_delete.router)
router.include_router(products_save.router)
router.include_router(products_check_dup.router)
router.include_router(forms_add.router)
router.include_router(forms_edit.router)
router.include_router(forms_copy.router)