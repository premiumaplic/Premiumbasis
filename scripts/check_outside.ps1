# Проверка: не появилось ли что-то от SchoolBot вне его папки.
# Запуск: check.bat (или автоматически в конце setup.bat).
# Результат: на экране и в файле data\check_outside.txt
param([string]$Root)

$ErrorActionPreference = 'SilentlyContinue'
[Console]::OutputEncoding = [Text.Encoding]::UTF8

if (-not $Root) { $Root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot) }
$rootFull = [IO.Path]::GetFullPath($Root).TrimEnd('\')
$data = Join-Path $rootFull 'data'
$since = (Get-Date).AddDays(-1)
$startFile = Join-Path $data 'setup_started.txt'
if (Test-Path $startFile) { $since = [DateTime]::Parse((Get-Content $startFile -Raw).Trim()) }

function Inside($path) { return $path.StartsWith($rootFull + '\', [StringComparison]::OrdinalIgnoreCase) }

$found = @()
$info = @()

# 1) Места, куда Python, pip, uv и matplotlib пишут по умолчанию
$places = @(
    "$env:APPDATA\Python", "$env:LOCALAPPDATA\Python", "$env:LOCALAPPDATA\Programs\Python",
    "$env:LOCALAPPDATA\pip", "$env:APPDATA\pip", "$env:USERPROFILE\pip",
    "$env:LOCALAPPDATA\uv", "$env:APPDATA\uv",
    "$env:USERPROFILE\.matplotlib", "$env:LOCALAPPDATA\matplotlib", "$env:USERPROFILE\.config\matplotlib",
    "$env:USERPROFILE\.cache"
)
foreach ($p in $places) {
    if ((Test-Path $p) -and -not (Inside $p)) {
        $new = @(Get-ChildItem $p -Recurse -File -Force | Where-Object { $_.LastWriteTime -ge $since })
        if ($new.Count -gt 0) { $found += "$p (изменено файлов после установки: $($new.Count))" }
        else { $info += "$p существует, но после установки не менялась (это от другой программы)" }
    }
}

# 2) Временная папка Windows: свежие файлы, похожие на наши
$sysTemp = [Environment]::GetEnvironmentVariable('TEMP', 'User')
if (-not $sysTemp) { $sysTemp = "$env:LOCALAPPDATA\Temp" }
$sysTemp = [Environment]::ExpandEnvironmentVariables($sysTemp)
if ((Test-Path $sysTemp) -and -not (Inside $sysTemp)) {
    $pattern = '(?i)(pip|python|matplotlib|get-pip|aiogram|numpy|pyzipper|openpyxl|schoolbot)'
    $new = @(Get-ChildItem $sysTemp -Recurse -Force | Where-Object { $_.LastWriteTime -ge $since -and $_.FullName -match $pattern })
    foreach ($f in ($new | Select-Object -First 20)) { $found += "$($f.FullName)" }
}

# 3) Новые папки прямо в профиле пользователя (например .matplotlib)
foreach ($d in (Get-ChildItem $env:USERPROFILE -Directory -Force | Where-Object { $_.CreationTime -ge $since })) {
    if (-not (Inside $d.FullName)) { $info += "в профиле появилась папка $($d.FullName) — проверьте, не от SchoolBot ли она" }
}

# 4) Реестр: Python, установленный обычным способом, записывает себя сюда
if (Test-Path 'HKCU:\Software\Python') {
    $info += 'в реестре есть раздел HKCU\Software\Python — его создаёт обычный установщик Python, наш переносной Python его не создаёт'
}

$lines = @()
if ($found.Count -eq 0) { $lines += 'Вне папки ничего не найдено ✅' }
else { $lines += "Найдено вне папки: $($found.Count) ❌ (список ниже)" }
$lines += "Папка: $rootFull"
$lines += "Проверялись изменения после: $($since.ToString('dd.MM.yyyy HH:mm'))"
$sizeMb = [math]::Round(((Get-ChildItem $rootFull -Recurse -File -Force | Measure-Object Length -Sum).Sum / 1MB))
$lines += "Размер папки: $sizeMb МБ"
foreach ($f in $found) { $lines += "  ❌ $f" }
foreach ($i in $info) { $lines += "  ℹ $i" }

$lines | ForEach-Object { Write-Host $_ }
New-Item -ItemType Directory -Force -Path $data | Out-Null
$lines | Set-Content -Encoding UTF8 (Join-Path $data 'check_outside.txt')
