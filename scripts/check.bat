@echo off
rem SchoolBot - проверка, что вне папки ничего не появилось.
setlocal
chcp 65001 >nul
set "SB_ROOT=%~dp0"
if "%SB_ROOT:~-1%"=="\" set "SB_ROOT=%SB_ROOT:~0,-1%"
powershell -NoProfile -ExecutionPolicy Bypass -File "%SB_ROOT%\app\scripts\check_outside.ps1" -Root "%SB_ROOT%"
echo.
echo Результат сохранён в data\check_outside.txt
pause
