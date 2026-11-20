@echo off
rem ============================================================
rem  SchoolBot - восстановление базы из бэкапа.
rem  Сначала закройте окно бота. Текущая база будет сохранена рядом.
rem ============================================================
setlocal
chcp 65001 >nul
set "SB_ROOT=%~dp0"
if "%SB_ROOT:~-1%"=="\" set "SB_ROOT=%SB_ROOT:~0,-1%"
cd /d "%SB_ROOT%"
set "TEMP=%SB_ROOT%\data\tmp"
set "TMP=%SB_ROOT%\data\tmp"
set "PYTHONNOUSERSITE=1"
set "PYTHONUTF8=1"
set "PYTHONIOENCODING=utf-8"
title SchoolBot - восстановление из бэкапа
if not exist "%SB_ROOT%\python\python.exe" (
  echo Не найден Python. Сначала запустите setup.bat
  pause
  exit /b 1
)
"%SB_ROOT%\python\python.exe" -m bot.tools restore
echo.
pause
