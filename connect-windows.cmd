@echo off
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel% equ 0 (
  py -3 connect_pinterest.py
) else (
  python connect_pinterest.py
)
pause
