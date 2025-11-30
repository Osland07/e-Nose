@echo off
echo Membuka Aplikasi E-Nose...
echo Mohon tunggu sebentar...

cd /d "%~dp0"
".venv\Scripts\python.exe" main.py

if %errorlevel% neq 0 (
    echo.
    echo TERJADI ERROR!
    echo Silakan foto pesan error di atas.
    pause
)
