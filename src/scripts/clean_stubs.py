import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from src.db import get_conn

def main():
    with get_conn() as conn:
        # Находим все заглушки
        stubs = conn.execute("""
            SELECT productId FROM products 
            WHERE name LIKE 'Товар %' OR baseGameName LIKE 'Товар %'
        """).fetchall()
        
        if not stubs:
            print("Заглушек не найдено.")
            return

        deleted = 0

        for row in stubs:
            pid = row["productId"]
            
            # Удаляем позиции заказов (если вдруг они есть)
            conn.execute("DELETE FROM salesOrderItems WHERE productId = ?", (pid,))
            # Удаляем листинги
            conn.execute("DELETE FROM listings WHERE productId = ?", (pid,))
            # Удаляем сам товар
            conn.execute("DELETE FROM products WHERE productId = ?", (pid,))
            
            deleted += 1

        conn.commit()
        print(f"Удалено заглушек: {deleted}")

if __name__ == "__main__":
    main()