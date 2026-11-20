@echo off
rem ============================================================
rem  SchoolBot - тестовый бот этапа 0.
rem  Окно должно оставаться открытым. Закрыли окно - бот остановлен.
rem ============================================================
setlocal
chcp 65001 >nul
set "SB_ROOT=%~dp0"
if "%SB_ROOT:~-1%"=="\" set "SB_ROOT=%SB_ROOT:~0,-1%"
cd /d "%SB_ROOT%"
rem Всё временное и все кэши - только внутри папки
set "TEMP=%SB_ROOT%\data\tmp"
set "TMP=%SB_ROOT%\data\tmp"
set "MPLCONFIGDIR=%SB_ROOT%\data\mpl"
set "PYTHONNOUSERSITE=1"
set "PYTHONUTF8=1"
set "PYTHONIOENCODING=utf-8"
title SchoolBot - тестовый бот (этап 0)

if not exist "%SB_ROOT%\python\python.exe" (
  echo Не найден Python. Сначала запустите setup.bat
  pause
  exit /b 1
)

:loop
"%SB_ROOT%\python\python.exe" -m bot.probe_bot
if "%ERRORLEVEL%"=="2" (
  echo Исправьте config.ini и запустите probe.bat снова.
  pause
  exit /b 2
)
echo.
echo Бот остановился. Перезапуск через 10 секунд. Чтобы остановить совсем - закройте окно.
timeout /t 10 /nobreak >nul
goto loop
