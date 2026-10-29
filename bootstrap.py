import subprocess
import sys
import os
from pathlib import Path

# Цвета для вывода (работают в большинстве терминалов)
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
RESET = '\033[0m'

def run_step(name, command, critical=True):
    """Запускает команду и выводит результат с галочкой."""
    print(f"\n{YELLOW}▶ {name}...{RESET}")
    try:
        result = subprocess.run(command, check=True, text=True, capture_output=False)
        print(f"{GREEN}✅ {name} — выполнено{RESET}")
        return True
    except subprocess.CalledProcessError as e:
        if critical:
            print(f"\n{RED}❌ ОШИБКА в шаге: {name}{RESET}")
            print(f"{RED}Команда: {' '.join(command)}{RESET}")
            print(f"{RED}Код возврата: {e.returncode}{RESET}")
            print(f"\n{RED}🚨 ALERT! STOP! Вызовите администратора!{RESET}")
            sys.exit(1)
        else:
            print(f"{YELLOW}⚠️ {name} — пропущено (не критично){RESET}")
            return False

def main():
    print(f"{YELLOW}🚀 Запуск bootstrap пайплайна Only_limited_magazin{RESET}")
    
    # --- ПРОВЕРКА VENV ---
    # Если мы не в venv (нет переменной VIRTUAL_ENV), пытаемся его активировать
    if not os.environ.get("VIRTUAL_ENV"):
        print(f"{YELLOW}⚠️ Виртуальное окружение не активировано. Пытаюсь активировать...{RESET}")
        
        # Ищем venv в корне проекта
        venv_path = Path("venv")
        if not venv_path.exists():
            print(f"{RED}❌ Ошибка: папка venv не найдена. Создайте окружение: python -m venv venv{RESET}")
            sys.exit(1)
        
        # Для Windows
        if os.name == "nt":
            activate_script = venv_path / "Scripts" / "activate"
            # Запускаем bootstrap заново, но уже через активированный python
            python_exe = venv_path / "Scripts" / "python.exe"
            if not python_exe.exists():
                print(f"{RED}❌ Ошибка: python.exe не найден в venv{RESET}")
                sys.exit(1)
            # Перезапускаем скрипт через venv python
            print(f"{YELLOW}🔄 Перезапуск через venv...{RESET}")
            os.execv(str(python_exe), [str(python_exe), __file__])
        else:
            # Для Linux/Mac
            python_exe = venv_path / "bin" / "python"
            if not python_exe.exists():
                print(f"{RED}❌ Ошибка: python не найден в venv{RESET}")
                sys.exit(1)
            print(f"{YELLOW}🔄 Перезапуск через venv...{RESET}")
            os.execv(str(python_exe), [str(python_exe), __file__])
    
    print(f"{GREEN}✅ Виртуальное окружение активно{RESET}")

    print(f"{YELLOW}🚀 Запуск bootstrap пайплайна Only_limited_magazin{RESET}")
    
    # Проверяем, что мы в корне проекта (есть папка src)
    if not Path("src").exists():
        print(f"{RED}❌ Ошибка: запустите скрипт из корня проекта (там, где папка src){RESET}")
        sys.exit(1)
    
    # 1. Инициализация БД
    run_step("Инициализация БД", ["python", "-m", "src.scripts.init_db"])
    
    # 2. Заполнение справочников
    run_step("Заполнение справочников", ["python", "-m", "src.scripts.seed_reference_data"])
    
    # 3. Добавление магазинов и склада
    run_step("Добавление магазинов и склада", ["python", "add_stores.py"])
    
    # 4. Загрузка товаров (два магазина)
    run_step("Загрузка товаров (LimitedGames)", ["python", "-m", "src.scripts.fetch_products", "limited_games"])
    run_step("Загрузка товаров (Console Games)", ["python", "-m", "src.scripts.fetch_products", "console_games"])
    
    # 5. Удаление заглушек
    run_step("Удаление заглушек", ["python", "-m", "src.scripts.clean_stubs"], critical=False)
    
    # 6. Загрузка цен и остатков
    run_step("Загрузка цен (LimitedGames)", ["python", "-m", "src.scripts.fetch_product_details", "limited_games"])
    run_step("Загрузка цен (Console Games)", ["python", "-m", "src.scripts.fetch_product_details", "console_games"])
    
    # 7. Загрузка истории продаж (пример за 2026 год, можно расширить)
    run_step("Загрузка продаж (LimitedGames 2026)", ["python", "-m", "src.scripts.fetch_postings", "limited_games", "2026-01-01", "2026-12-31"])
    run_step("Загрузка продаж (Console Games 2026)", ["python", "-m", "src.scripts.fetch_postings", "console_games", "2026-01-01", "2026-12-31"])
    
    # 8. Парсинг названий
    run_step("Парсинг названий", ["python", "-m", "src.scripts.parse_names"])
    
    # 9. Склейка дублей (пока в разработке)
    run_step("Склейка дублей (отложено)", ["python", "-m", "src.scripts.merge_duplicates"], critical=False)
    
    print(f"\n{GREEN}🎉 Все шаги выполнены успешно!{RESET}")

if __name__ == "__main__":
    main()