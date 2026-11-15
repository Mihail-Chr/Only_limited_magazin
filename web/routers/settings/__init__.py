"""
settings — пакет роутеров Настроек (v3.1).
"""
from fastapi import APIRouter

from . import (
    menu,
    stores,
    run_action,
    update_item,
    backup,
    restore,
    history,  # <-- Добавили
    refs,     # <-- Добавили
)

router = APIRouter(prefix="/settings", tags=["settings"])

router.include_router(menu.router)
router.include_router(stores.router)
router.include_router(run_action.router)
router.include_router(update_item.router)
router.include_router(backup.router)
router.include_router(restore.router)
router.include_router(history.router)  # <-- Добавили
router.include_router(refs.router)     # <-- Добавили