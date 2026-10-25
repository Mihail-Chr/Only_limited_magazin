import hashlib
import os
from src.config import settings
from src.db import get_conn


def _hash(p: str) -> str:
    return hashlib.sha256(p.encode("utf-8")).hexdigest()


def seed() -> None:
    with get_conn() as conn:
        # Роли
        for code, name in [
            ("admin", "Администратор"),
            ("warehouse_keeper", "Кладовщик"),
            ("seller", "Продавец"),
            ("auditor", "Аудитор"),
        ]:
            conn.execute(
                "INSERT OR IGNORE INTO role(code, name) VALUES(?, ?)", (code, name)
            )

        # Склады
        for w in settings.warehouses:
            conn.execute(
                "INSERT OR IGNORE INTO warehouse(code, name, default_currency) VALUES(?, ?, ?)",
                (w.code, w.name, w.default_currency),
            )
            wid = conn.execute(
                "SELECT id FROM warehouse WHERE code=?", (w.code,)
            ).fetchone()["id"]
            for cur in w.supported_currencies:
                conn.execute(
                    "INSERT OR IGNORE INTO warehouse_currency(warehouse_id, currency) VALUES(?, ?)",
                    (wid, cur),
                )

        # Магазины
        for s in settings.stores:
            conn.execute(
                """INSERT INTO store(code, name, client_id, api_key, has_api, is_active, api_role)
                   VALUES(?, ?, ?, ?, ?, ?, ?)
                   ON CONFLICT(code) DO UPDATE SET
                     name=excluded.name,
                     client_id=excluded.client_id,
                     api_key=excluded.api_key,
                     has_api=excluded.has_api,
                     is_active=excluded.is_active,
                     api_role=excluded.api_role""",
                (
                    s.code,
                    s.name,
                    s.client_id,
                    s.api_key,
                    1 if s.has_api else 0,
                    1 if s.is_active else 0,
                    s.api_role,
                ),
            )

        def get_role(code: str) -> int:
            return conn.execute(
                "SELECT id FROM role WHERE code=?", (code,)
            ).fetchone()["id"]

        def upsert_user(login: str, email: str | None, password: str) -> int:
            existing = conn.execute(
                "SELECT id FROM app_user WHERE login=?", (login,)
            ).fetchone()
            if existing:
                return existing["id"]
            cur = conn.execute(
                "INSERT INTO app_user(login, email, password_hash) VALUES(?, ?, ?)",
                (login, email, _hash(password)),
            )
            return cur.lastrowid

        # Админ
        admin_id = upsert_user(
            os.getenv("SEED_ADMIN_LOGIN", "admin"),
            os.getenv("SEED_ADMIN_EMAIL"),
            os.getenv("SEED_ADMIN_PASSWORD", "change_me"),
        )
        conn.execute(
            "INSERT OR IGNORE INTO user_role(user_id, role_id) VALUES(?, ?)",
            (admin_id, get_role("admin")),
        )

        # Кладовщик (может быть на нескольких складах)
        keeper_login = os.getenv("SEED_WAREHOUSE_KEEPER_LOGIN")
        if keeper_login:
            keeper_id = upsert_user(
                keeper_login,
                os.getenv("SEED_WAREHOUSE_KEEPER_EMAIL"),
                os.getenv("SEED_WAREHOUSE_KEEPER_PASSWORD", "change_me"),
            )
            conn.execute(
                "INSERT OR IGNORE INTO user_role(user_id, role_id) VALUES(?, ?)",
                (keeper_id, get_role("warehouse_keeper")),
            )
            wh_codes = [
                c.strip()
                for c in os.getenv("SEED_WAREHOUSE_KEEPER_WAREHOUSES", "").split(";")
                if c.strip()
            ]
            for code in wh_codes:
                row = conn.execute(
                    "SELECT id FROM warehouse WHERE code=?", (code,)
                ).fetchone()
                if row:
                    conn.execute(
                        "INSERT OR IGNORE INTO user_warehouse(user_id, warehouse_id) VALUES(?, ?)",
                        (keeper_id, row["id"]),
                    )

        # Продавцы
        for i in (1, 2):
            login = os.getenv(f"SEED_SELLER_{i}_LOGIN")
            if not login:
                continue
            seller_id = upsert_user(
                login,
                os.getenv(f"SEED_SELLER_{i}_EMAIL"),
                os.getenv(f"SEED_SELLER_{i}_PASSWORD", "change_me"),
            )
            conn.execute(
                "INSERT OR IGNORE INTO user_role(user_id, role_id) VALUES(?, ?)",
                (seller_id, get_role("seller")),
            )
            store_code = os.getenv(f"SEED_SELLER_{i}_STORE_CODE")
            if store_code:
                row = conn.execute(
                    "SELECT id FROM store WHERE code=?", (store_code,)
                ).fetchone()
                if row:
                    conn.execute(
                        "INSERT OR IGNORE INTO user_store(user_id, store_id) VALUES(?, ?)",
                        (seller_id, row["id"]),
                    )

        # Аудитор
        auditor_login = os.getenv("SEED_AUDITOR_LOGIN")
        if auditor_login:
            auditor_id = upsert_user(
                auditor_login,
                os.getenv("SEED_AUDITOR_EMAIL"),
                os.getenv("SEED_AUDITOR_PASSWORD", "change_me"),
            )
            conn.execute(
                "INSERT OR IGNORE INTO user_role(user_id, role_id) VALUES(?, ?)",
                (auditor_id, get_role("auditor")),
            )

        conn.commit()


if __name__ == "__main__":
    seed()
    print("Seed выполнен")