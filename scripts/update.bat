@echo off
rem ============================================================
rem  SchoolBot - обновление программы.
rem  Сначала закройте окно бота. База и config.ini не трогаются.
rem ============================================================
setlocal
chcp 65001 >nul
set "SB_SELF=%~f0"
set "SB_ROOT=%~dp0"
if "%SB_ROOT:~-1%"=="\" set "SB_ROOT=%SB_ROOT:~0,-1%"
powershell -NoProfile -ExecutionPolicy Bypass -Command "$t=[IO.File]::ReadAllText($env:SB_SELF,[Text.Encoding]::UTF8); iex $t.Substring($t.IndexOf('#'+'#PS-BEGIN'))"
set "RC=%ERRORLEVEL%"
echo.
pause
exit /b %RC%

##PS-BEGIN
# ---- Дальше команды PowerShell (их выполняет строка powershell выше) ----
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
[Console]::OutputEncoding = [Text.Encoding]::UTF8
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

$REPO   = 'premiumaplic/Premiumbasis'
$BRANCH = ''                          # пусто = основная ветка репозитория

$root  = $env:SB_ROOT
$app   = Join-Path $root 'app'
$py    = Join-Path $root 'python'
$data  = Join-Path $root 'data'
$tmp   = Join-Path $data 'tmp'
$pyExe = Join-Path $py 'python.exe'
$old   = Join-Path $tmp 'app-old'

function Step($text) { Write-Host ''; Write-Host "== $text" -ForegroundColor Cyan }
function Fail($text) {
    Write-Host ''
    Write-Host "ОШИБКА: $text" -ForegroundColor Red
    Write-Host 'Обновление остановлено. Сфотографируйте это окно и пришлите разработчику.'
    exit 1
}
function Download($url, $file) {
    $wc = New-Object Net.WebClient
    $wc.Headers.Add('User-Agent', 'SchoolBot-update')
    $wc.DownloadFile($url, $file)
}
function Unzip($zip, $dest) {
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    if (Test-Path $dest) { Remove-Item $dest -Recurse -Force }
    [IO.Compression.ZipFile]::ExtractToDirectory($zip, $dest)
}
function RunPy {
    # Вывод Python — сразу на экран, а функция возвращает только «успешно / нет»
    & $pyExe @args | Out-Host
    return ($LASTEXITCODE -eq 0)
}
function RollBack($why) {
    Write-Host "Возвращаю прежнюю версию программы..." -ForegroundColor Yellow
    if (Test-Path $old) {
        if (Test-Path $app) { Remove-Item $app -Recurse -Force }
        Move-Item $old $app
    }
    Fail $why
}

try {
    if (-not (Test-Path $pyExe)) { Fail 'не найден Python. Сначала запустите setup.bat.' }
    New-Item -ItemType Directory -Force -Path $tmp | Out-Null
    $env:TEMP = $tmp; $env:TMP = $tmp
    $env:PIP_CACHE_DIR = Join-Path $py 'pip-cache'
    $env:PIP_DISABLE_PIP_VERSION_CHECK = '1'
    $env:PIP_NO_WARN_SCRIPT_LOCATION = '1'
    $env:PYTHONNOUSERSITE = '1'
    $env:PYTHONUTF8 = '1'
    $env:MPLCONFIGDIR = Join-Path $data 'mpl'

    # ---------- 1. Бот должен быть остановлен ----------
    Step 'Проверяю, что бот остановлен'
    $lock = Join-Path $data 'bot.lock'
    if (Test-Path $lock) {
        $fs = [IO.File]::Open($lock, 'Open', 'ReadWrite', 'ReadWrite')
        try { $fs.Lock(0, 1); $fs.Unlock(0, 1) }
        catch { $fs.Close(); Fail 'бот ещё работает. Закройте окно бота и запустите update.bat снова.' }
        $fs.Close()
    }
    Write-Host 'Бот остановлен.'

    # ---------- 2. Копия базы ----------
    Step 'Делаю копию базы'
    if (-not (RunPy -m bot.tools backup before-update)) { Fail 'не удалось сделать копию базы — обновление не начато.' }

    # ---------- 3. Новая версия программы ----------
    Step 'Скачиваю новую версию программы'
    $codeZip = Join-Path $tmp 'code.zip'
    $codeDir = Join-Path $tmp 'code'
    $url = "https://api.github.com/repos/$REPO/zipball"
    if ($BRANCH) { $url = "$url/$BRANCH" }
    Download $url $codeZip
    Unzip $codeZip $codeDir
    $inner = Get-ChildItem $codeDir -Directory | Select-Object -First 1
    if (-not $inner -or -not (Test-Path (Join-Path $inner.FullName 'bot'))) { Fail 'в скачанном архиве нет программы.' }
    if (Test-Path $old) { Remove-Item $old -Recurse -Force }
    Move-Item $app $old
    Move-Item $inner.FullName $app
    Remove-Item $codeZip, $codeDir -Recurse -Force -ErrorAction SilentlyContinue
    Write-Host 'Программа обновлена.'

    # ---------- 4. Библиотеки и база ----------
    Step 'Обновляю библиотеки'
    if (-not (RunPy -m pip install --only-binary=:all: -r (Join-Path $app 'requirements.txt'))) {
        RollBack 'не удалось обновить библиотеки.'
    }
    Remove-Item $env:PIP_CACHE_DIR -Recurse -Force -ErrorAction SilentlyContinue
    Step 'Обновляю базу'
    if (-not (RunPy -m bot.tools migrate)) { RollBack 'не удалось обновить базу (база не изменена).' }

    # ---------- 5. Файлы запуска ----------
    foreach ($f in @('start.bat', 'check.bat', 'probe.bat')) {
        Copy-Item (Join-Path $app "scripts\$f") (Join-Path $root $f) -Force
    }
    # update.bat сейчас выполняется, поэтому новая версия заменит его при следующем запуске start.bat
    Copy-Item (Join-Path $app 'scripts\update.bat') (Join-Path $root 'update.bat.new') -Force
    Remove-Item $old -Recurse -Force -ErrorAction SilentlyContinue

    # ---------- 6. Запуск ----------
    Step 'Запускаю бота'
    Start-Process -FilePath (Join-Path $root 'start.bat') -WorkingDirectory $root
    Write-Host 'Готово. Бот запущен в новом окне. Это окно можно закрыть.' -ForegroundColor Green
    exit 0
}
catch {
    if ((Test-Path $old) -and -not (Test-Path $app)) { RollBack $_.Exception.Message }
    Fail $_.Exception.Message
}
