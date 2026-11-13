@echo off
REM Peak Season Admin Studio: opens in the browser at http://localhost:8765 (or the next free port)
cd /d "%~dp0"
where python >nul 2>nul && (python studio.py) || (py -3 studio.py)
pause
