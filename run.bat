@echo off
REM run.bat — активирует venv и запускает команду (для разработки)
cd /d "%~dp0"
if not exist "venv\Scripts\activate.bat" (
    echo [ERROR] venv не найден
    exit /b 1
)
call venv\Scripts\activate.bat
%*
call deactivate