@echo off
cd /d "%~dp0"
set PYTHONUTF8=1
python -m kk_tool
echo.
echo Si la ventana no se abrio, copia el mensaje de arriba.
pause
