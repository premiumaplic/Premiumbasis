@echo off
rem ============================================================
rem  SchoolBot - установка. Запускается ОДИН раз.
rem  Положите этот файл в пустую папку (например D:\SchoolBot)
rem  и запустите двойным щелчком. Права администратора не нужны.
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

# ---- Настройки установки ----
$PY_VERSION = '3.15.2'                    # версия Python (закреплена)
$REPO       = 'premiumaplic/Premiumbasis' # откуда берётся код
$BRANCH     = ''                          # пусто = основная ветка репозитория

$root   = $env:SB_ROOT
$app    = Join-Path $root 'app'
$py     = Join-Path $root 'python'
$data   = Join-Path $root 'data'
$tmp    = Join-Path $data 'tmp'
$pyExe  = Join-Path $py 'python.exe'

function Step($text) { Write-Host ''; Write-Host "== $text" -ForegroundColor Cyan }
function Fail($text) {
    Write-Host ''
    Write-Host "ОШИБКА: $text" -ForegroundColor Red
    Write-Host 'Установка остановлена. Сфотографируйте это окно и пришлите разработчику.'
    exit 1
}
function Download($urls, $file, $what) {
    # Пробуем адреса по очереди: если один сервер отказал, берём запасной
    $last = ''
    foreach ($url in @($urls)) {
        Write-Host "   скачиваю: $url"
        try {
            $wc = New-Object Net.WebClient
            $wc.Headers.Add('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) SchoolBot-setup')
            $wc.DownloadFile($url, $file)
            return $url
        } catch {
            $last = $_.Exception.InnerException.Message
            if (-not $last) { $last = $_.Exception.Message }
            Write-Host "   не получилось: $last" -ForegroundColor Yellow
        }
    }
    Fail "не удалось скачать $what ни с одного адреса. Проверьте интернет и попробуйте через час. Ошибка: $last"
}
function Unzip($zip, $dest) {
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    if (Test-Path $dest) { Remove-Item $dest -Recurse -Force }
    [IO.Compression.ZipFile]::ExtractToDirectory($zip, $dest)
}
function RunPy {
    & $pyExe @args
    if ($LASTEXITCODE -ne 0) { Fail "команда Python завершилась с ошибкой ($LASTEXITCODE)" }
}

try {
    Write-Host "Установка SchoolBot в папку $root"

    # ---------- 1. Проверки ----------
    Step 'Проверяю папку'
    if ($root -match '[^\x21-\x7E]') {
        Fail "в пути к папке есть пробелы или русские буквы: $root`nСоздайте папку вроде D:\SchoolBot и запустите setup.bat оттуда."
    }
    if ((Test-Path (Join-Path $root 'bot')) -or (Test-Path (Join-Path $root '..\bot'))) {
        Fail 'похоже, setup.bat запущен из скачанной копии кода. Скопируйте setup.bat в пустую папку (например D:\SchoolBot) и запустите там.'
    }
    $free = (New-Object IO.DriveInfo ([IO.Path]::GetPathRoot($root))).AvailableFreeSpace
    if ($free -lt 1GB) { Fail 'на диске меньше 1 ГБ свободного места.' }
    Write-Host 'Папка подходит.'

    foreach ($d in @($py, $data, $tmp, (Join-Path $data 'logs'), (Join-Path $data 'backups'), (Join-Path $data 'mpl'))) {
        New-Item -ItemType Directory -Force -Path $d | Out-Null
    }
    $startFile = Join-Path $data 'setup_started.txt'
    if (-not (Test-Path $startFile)) {
        (Get-Date).ToString('o') | Set-Content -Encoding ASCII $startFile
    }

    # Всё временное и все кэши — только внутри папки
    $env:TEMP = $tmp
    $env:TMP = $tmp
    $env:PIP_CACHE_DIR = Join-Path $py 'pip-cache'
    $env:PIP_DISABLE_PIP_VERSION_CHECK = '1'
    $env:PIP_NO_WARN_SCRIPT_LOCATION = '1'
    $env:PYTHONNOUSERSITE = '1'
    $env:PYTHONUTF8 = '1'
    $env:MPLCONFIGDIR = Join-Path $data 'mpl'
    $env:SB_ROOT = $root

    # ---------- 2. Код программы ----------
    Step 'Скачиваю программу с GitHub'
    $codeZip = Join-Path $tmp 'code.zip'
    $codeDir = Join-Path $tmp 'code'
    # Основной адрес — обычный архив GitHub; служебный API (лимит 60 запросов в час) — запасной
    $ref = 'HEAD'
    if ($BRANCH) { $ref = $BRANCH }
    $codeUrls = @("https://github.com/$REPO/archive/$ref.zip",
                  "https://codeload.github.com/$REPO/zip/$ref",
                  "https://api.github.com/repos/$REPO/zipball/$ref")
    Download $codeUrls $codeZip 'программу с GitHub' | Out-Null
    Unzip $codeZip $codeDir
    $inner = Get-ChildItem $codeDir -Directory | Select-Object -First 1
    if (-not $inner -or -not (Test-Path (Join-Path $inner.FullName 'bot'))) { Fail 'в скачанном архиве нет программы.' }
    if (Test-Path $app) { Remove-Item $app -Recurse -Force }
    Move-Item $inner.FullName $app
    Remove-Item $codeZip, $codeDir -Recurse -Force -ErrorAction SilentlyContinue
    Write-Host 'Программа скачана в папку app.'

    # ---------- 3. Переносной Python ----------
    Step "Устанавливаю Python $PY_VERSION (переносной, только в эту папку)"
    $haveVersion = ''
    if (Test-Path $pyExe) { $haveVersion = (& $pyExe -c "import platform;print(platform.python_version())") }
    if ($haveVersion -ne $PY_VERSION) {
        if (Test-Path $py) { Remove-Item $py -Recurse -Force }
        $pyZip = Join-Path $tmp 'python.zip'
        # Основной источник — python.org (embeddable), запасной — официальный пакет Python на NuGet
        $used = Download @("https://www.python.org/ftp/python/$PY_VERSION/python-$PY_VERSION-embed-amd64.zip",
                           "https://api.nuget.org/v3-flatcontainer/python/$PY_VERSION/python.$PY_VERSION.nupkg") $pyZip 'Python'
        $short = 'python' + (($PY_VERSION -split '\.')[0..1] -join '')
        if ($used -like '*.nupkg') {
            $unpacked = Join-Path $tmp 'python-nuget'
            Unzip $pyZip $unpacked
            Move-Item (Join-Path $unpacked 'tools') $py
            Remove-Item $unpacked -Recurse -Force
            # Файл ._pth задаёт, где Python ищет модули: только внутри нашей папки
            Set-Content -Encoding ASCII -Path (Join-Path $py "$short._pth") -Value @('Lib', 'DLLs', '.', '..\app', 'Lib\site-packages', 'import site')
        } else {
            Unzip $pyZip $py
            $pth = Get-ChildItem (Join-Path $py 'python*._pth') | Select-Object -First 1
            $stdZip = (Get-ChildItem (Join-Path $py 'python*.zip') | Select-Object -First 1).Name
            Set-Content -Encoding ASCII -Path $pth.FullName -Value @($stdZip, '.', '..\app', 'Lib\site-packages', 'import site')
        }
        Remove-Item $pyZip -Force
        Write-Host 'Python распакован.'
    } else {
        Write-Host 'Python уже установлен.'
    }

    # ---------- 4. Библиотеки ----------
    Step 'Устанавливаю библиотеки (несколько минут)'
    $ErrorActionPreference = 'Continue'   # иначе сообщение «pip не найден» остановит установку
    & $pyExe -m pip --version *> $null
    $pipMissing = ($LASTEXITCODE -ne 0)
    $ErrorActionPreference = 'Stop'
    if ($pipMissing) {
        $getPip = Join-Path $tmp 'get-pip.py'
        Download @('https://bootstrap.pypa.io/get-pip.py', 'https://bootstrap.pypa.io/pip/get-pip.py') $getPip 'установщик pip' | Out-Null
        RunPy $getPip
        Remove-Item $getPip -Force
    }
    RunPy -m pip install --only-binary=:all: -r (Join-Path $app 'requirements.txt')
    Remove-Item $env:PIP_CACHE_DIR -Recurse -Force -ErrorAction SilentlyContinue

    # ---------- 5. Проверка ----------
    Step 'Проверяю установку'
    RunPy -m bot.selfcheck

    # ---------- 6. Файлы запуска и настройки ----------
    Step 'Готовлю файлы запуска'
    foreach ($f in @('start.bat', 'update.bat', 'restore.bat', 'check.bat', 'probe.bat')) {
        Copy-Item (Join-Path $app "scripts\$f") (Join-Path $root $f) -Force
    }
    $cfg = Join-Path $root 'config.ini'
    $newConfig = -not (Test-Path $cfg)
    if ($newConfig) { Copy-Item (Join-Path $app 'config.example.ini') $cfg }

    # ---------- 7. Ничего ли не появилось вне папки ----------
    Step 'Проверяю, что вне папки ничего не появилось'
    & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $app 'scripts\check_outside.ps1') -Root $root

    $sizeMb = [math]::Round(((Get-ChildItem $root -Recurse -File -Force | Measure-Object Length -Sum).Sum / 1MB))
    Write-Host ''
    Write-Host "Установка завершена. Размер папки: $sizeMb МБ." -ForegroundColor Green
    Write-Host ''
    Write-Host 'Что нужно вписать в config.ini (он сейчас откроется в Блокноте):'
    Write-Host '  1) token    - токен бота от @BotFather'
    Write-Host '  2) owner_id - ваш Telegram ID. Если не знаете: запустите start.bat,'
    Write-Host '                напишите боту /myid, впишите номер и перезапустите start.bat'
    Write-Host 'Сохраните файл (Ctrl+S) и запустите start.bat.'
    if ($newConfig) { Start-Process notepad.exe $cfg }
    exit 0
}
catch {
    Fail $_.Exception.Message
}
