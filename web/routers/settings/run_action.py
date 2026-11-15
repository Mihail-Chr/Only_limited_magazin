"""
settings/run_action.py — POST /settings/run_action.

Запускает CLI-скрипты:
- load_products  → src/scripts/fetch_products.py <platform> <store_code>
- load_postings  → src/scripts/fetch_postings.py <platform> <store_code> <from> <to>
"""
import os
import subprocess
import sys
import time
from pathlib import Path

from fastapi import APIRouter, Form

router = APIRouter()


@router.post("/run_action")
def run_action(
    platform: str = Form(...),
    store_code: str = Form(...),
    action: str = Form(...),
):
    try:
        project_root = Path(__file__).resolve().parent.parent.parent.parent
        python_exe = sys.executable

        env = os.environ.copy()
        env["PYTHONPATH"] = str(project_root)

        if action == "load_products":
            script = project_root / "src" / "scripts" / "fetch_products.py"
            cmd = [python_exe, str(script), platform, store_code]
        elif action == "load_postings":
            today = time.strftime("%Y-%m-%d")
            year_ago = time.strftime(
                "%Y-%m-%d", time.localtime(time.time() - 365 * 24 * 3600)
            )
            script = project_root / "src" / "scripts" / "fetch_postings.py"
            cmd = [python_exe, str(script), platform, store_code, year_ago, today]
        else:
            return {"ok": False, "error": f"Неизвестное действие: {action}"}

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=str(project_root),
            env=env,
            timeout=300,
        )

        return {
            "ok": True,
            "message": f"Действие '{action}' выполнено (код {result.returncode})",
            "stdout": result.stdout[-3000:] if result.stdout else "",
            "stderr": result.stderr[-3000:] if result.stderr else "",
        }
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "Таймаут выполнения (более 5 минут)"}
    except Exception as e:
        return {"ok": False, "error": str(e)}