@echo off
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel% equ 0 (
  py -3 connect_pinterest_v2.py
) else (
  python connect_pinterest_v2.py
)
pause
