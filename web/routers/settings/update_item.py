"""
settings/update_item.py — POST /settings/update_item.

Редактирование справочников:
- warehouse  → warehouses.name
- platform   → platforms.platformName + platformVersion
- edition    → editionTypes.editionName (+ createdBy='manual', needsReview=0)
- publisher  → publishers.publisherName
- region     → regions.regionCode
"""
from fastapi import APIRouter, Form
from fastapi.responses import JSONResponse

from src.db import get_conn

router = APIRouter()


@router.post("/update_item")
def update_item(
    item_type: str = Form(...),
    item_id: int = Form(...),
    new_value: str = Form(...),
    new_version: str = Form(None),
):
    table_map = {
        "warehouse": ("warehouses", "warehouseId", "name"),
        "platform": ("platforms", "platformId", "platformName"),
        "edition": ("editionTypes", "editionId", "editionName"),
        "publisher": ("publishers", "publisherId", "publisherName"),
        "region": ("regions", "regionId", "regionCode"),
    }

    if item_type not in table_map:
        return JSONResponse({"ok": False, "error": f"Неизвестный тип: {item_type}"})

    table, id_field, value_field = table_map[item_type]

    with get_conn() as conn:
        conn.execute(
            f'UPDATE "{table}" SET "{value_field}" = ? WHERE "{id_field}" = ?',
            (new_value, item_id),
        )

        if item_type == "platform" and new_version is not None:
            conn.execute(
                f'UPDATE "{table}" SET "platformVersion" = ? WHERE "{id_field}" = ?',
                (new_version, item_id),
            )

        if item_type == "edition":
            conn.execute(
                'UPDATE "editionTypes" SET createdBy = ?, needsReview = 0 WHERE "editionId" = ?',
                ("manual", item_id),
            )

        conn.commit()

    return JSONResponse({"ok": True, "message": f"Обновлено: {new_value}"})