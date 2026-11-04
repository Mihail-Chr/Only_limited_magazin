@echo off
cd /d "%~dp0"
call venv\Scripts\activate.bat
uvicorn web.app:app --reload
pause