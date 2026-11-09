@echo off
REM run_test.bat — запускает тесты в venv
cd /d "%~dp0"
if not exist "venv\Scripts\activate.bat" (
    echo [ERROR] venv не найден
    exit /b 1
)
call venv\Scripts\activate.bat

REM Аргументы: если переданы — используем, иначе — все тесты
if "%~1"=="" (
    pytest tests/ -v
) else (
    pytest %*
)

call deactivate