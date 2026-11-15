"""
_shared/common.py — общие хелперы (JSON-ответы, приведение типов).
"""
from fastapi.responses import JSONResponse


def to_int_or_none(value):
    if value in ("", "None", None):
        return None
    try:
        return int(value)
    except (ValueError, TypeError):
        return None


def to_float_or_none(value):
    if value in ("", "None", None):
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def to_int_default(value, default=0):
    if value in ("", "None", None):
        return default
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def error(message: str, status_code: int = 400) -> JSONResponse:
    return JSONResponse({"ok": False, "error": message}, status_code=status_code)


def ok(**kwargs) -> JSONResponse:
    return JSONResponse({"ok": True, **kwargs})