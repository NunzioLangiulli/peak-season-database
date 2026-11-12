@echo off
REM Peak Season Admin Studio: si apre nel browser su http://localhost:8765 (o la porta libera successiva)
cd /d "%~dp0"
where python >nul 2>nul && (python studio.py) || (py -3 studio.py)
pause
