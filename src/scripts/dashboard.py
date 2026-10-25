"""
Единый дашборд для кладовщика, продавца и аудитора.
Запуск: python -m src.scripts.dashboard
"""
import os
import sys

# Добавляем корень проекта в путь, чтобы работали импорты
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.db import get_conn
from src.scripts import fetch_postings


def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')


def print_menu(role: str):
    print("\n" + "=" * 50)
    print(f" ВЫ ВОШЛИ КАК: {role.upper()}")
    print("=" * 50)
    print(" 1. Обновить данные с Ozon (заказы)")
    print(" 2. Показать мой рабочий экран")
    print(" 0. Выйти")
    print("=" * 50)


def keeper_screen():
    """Экран кладовщика: что собрать."""
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT p.posting_number, p.status, pi.offer_id, pi.name, pi.quantity
            FROM posting p
            JOIN posting_item pi ON pi.posting_id = p.id
            WHERE p.status NOT IN ('delivered', 'cancelled')
            ORDER BY p.created_at ASC
            """
        ).fetchall()

    if not rows:
        print("\n✅ Нет активных заказов для сборки. Всё отгружено!")
        return

    print("\n" + "=" * 80)
    print(" ЧТО НУЖНО СОБРАТЬ И ОТНЕСТИ В OZON")
    print("=" * 80)
    
    current = None
    for r in rows:
        if r["posting_number"] != current:
            current = r["posting_number"]
            print(f"\n📦 Отправление: {current} (статус: {r['status']})")
        name = (r["name"] or "")[:45] + "..." if len(r["name"] or "") > 45 else (r["name"] or "")
        print(f"   [{r['offer_id']}] {name} — {r['quantity']} шт.")


def seller_screen():
    """Экран продавца: цены, маржа, что нужно поправить."""
    with get_conn() as conn:
        # 1. Товары с самой низкой маржой
        risky = conn.execute(
            """
            SELECT p.offer_id, p.name, l.price, l.payout_amount, p.cost_price_synthetic,
                   CASE WHEN p.cost_price_synthetic > 0 AND l.payout_amount > 0
                        THEN ROUND((l.payout_amount - p.cost_price_synthetic) / l.payout_amount * 100, 1)
                        ELSE NULL END AS margin_net_pct
            FROM product p
            JOIN listing l ON l.product_id = p.id
            WHERE l.price IS NOT NULL AND l.price > 0
            ORDER BY margin_net_pct ASC
            LIMIT 10
            """
        ).fetchall()

        # 2. Товары, которые продаются (в пути)
        selling = conn.execute(
            """
            SELECT pi.offer_id, SUM(pi.quantity) AS qty
            FROM posting_item pi
            JOIN posting p ON p.id = pi.posting_id
            WHERE p.status NOT IN ('delivered', 'cancelled')
            GROUP BY pi.offer_id
            ORDER BY qty DESC
            LIMIT 10
            """
        ).fetchall()

    print("\n" + "=" * 80)
    print(" 🔴 ТОП-10 ТОВАРОВ С НИЗКОЙ ЧИСТОЙ МАРЖОЙ (требуют внимания)")
    print("=" * 80)
    print(f"{'Артикул':<8} | {'Цена':<8} | {'На руки':<8} | {'Маржа %':<7} | {'Название':<35}")
    print("-" * 80)
    for r in risky:
        name = (r["name"] or "")[:32] + "..." if len(r["name"] or "") > 35 else (r["name"] or "")
        print(f"{r['offer_id']:<8} | {r['price']:<8.2f} | {r['payout_amount']:<8.2f} | {r['margin_net_pct']:<7.1f} | {name}")

    print("\n" + "=" * 80)
    print(" 📦 ТОВАРЫ В ПУТИ (продажи)")
    print("=" * 80)
    for r in selling:
        print(f"   {r['offer_id']}: {r['qty']} шт.")


def auditor_screen():
    """Экран аудитора: общая сводка (только чтение)."""
    with get_conn() as conn:
        total_products = conn.execute("SELECT COUNT(*) FROM product").fetchone()[0]
        total_postings = conn.execute("SELECT COUNT(*) FROM posting").fetchone()[0]
        active_postings = conn.execute(
            "SELECT COUNT(*) FROM posting WHERE status NOT IN ('delivered', 'cancelled')"
        ).fetchone()[0]
        total_revenue = conn.execute(
            "SELECT COALESCE(SUM(pi.price * pi.quantity), 0) FROM posting_item pi JOIN posting p ON p.id = pi.posting_id"
        ).fetchone()[0]

    print("\n" + "=" * 80)
    print(" 📊 СВОДКА ДЛЯ АУДИТОРА (только чтение)")
    print("=" * 80)
    print(f" Всего товаров в базе:      {total_products}")
    print(f" Всего отправлений:         {total_postings}")
    print(f" Активных (не доставлено):  {active_postings}")
    print(f" Сумма по всем отправлениям: {total_revenue:,.2f} руб.")
    print("\n (Здесь можно добавить экспорт в Excel для аудита)")


def main():
    while True:  # Внешний цикл: выбор роли
        clear_screen()
        print("Добро пожаловать в систему Only Limited Magazin")
        print("Выберите роль:")
        print("1. Кладовщик")
        print("2. Продавец")
        print("3. Аудитор")
        print("0. Выйти из программы")
        choice = input("Ваш выбор (1/2/3/0): ").strip()

        if choice == "0":
            print("До встречи!")
            break

        if choice == "1":
            role = "Кладовщик"
            screen_func = keeper_screen
        elif choice == "2":
            role = "Продавец"
            screen_func = seller_screen
        elif choice == "3":
            role = "Аудитор"
            screen_func = auditor_screen
        else:
            print("Неверный выбор. Нажмите Enter...")
            input()
            continue

        # Внутренний цикл: работа внутри роли
        while True:
            clear_screen()
            print_menu(role)
            action = input("Действие: ").strip()

            if action == "0":
                # Возврат к выбору роли
                break
            elif action == "1":
                print("\n⏳ Обновляем данные с Ozon... (подождите)")
                fetch_postings.main()
                input("\nНажмите Enter, чтобы вернуться в меню...")
            elif action == "2":
                clear_screen()
                screen_func()
                input("\nНажмите Enter, чтобы вернуться в меню...")
            else:
                print("Неверное действие. Нажмите Enter...")
                input()


if __name__ == "__main__":
    main()