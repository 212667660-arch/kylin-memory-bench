param(
    [string]$VenvName = ".venv-kmb-windows"
)

$ErrorActionPreference = "Stop"
$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$Venv = Join-Path $Root $VenvName
$Temp = Join-Path $Root ".tmp-pip-windows"
$Cache = Join-Path $Root ".pip-cache-windows"
New-Item -ItemType Directory -Force -Path $Temp, $Cache | Out-Null

python -m venv --system-site-packages $Venv
$Python = Join-Path $Venv "Scripts\python.exe"
if (!(Test-Path -LiteralPath $Python)) { throw "virtualenv Python not found: $Python" }

$oldTemp = $env:TEMP; $oldTmp = $env:TMP; $oldCache = $env:PIP_CACHE_DIR
try {
    $env:TEMP = $Temp
    $env:TMP = $Temp
    $env:PIP_CACHE_DIR = $Cache
    & $Python "$Root\setup.py" develop
    & $Python "$Root\scripts\env_probe.py" --json
} finally {
    $env:TEMP = $oldTemp
    $env:TMP = $oldTmp
    $env:PIP_CACHE_DIR = $oldCache
}
Write-Output "installed environment: $Venv"
