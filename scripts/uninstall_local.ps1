param(
    [string]$VenvName = ".venv-kmb-windows"
)

$ErrorActionPreference = "Stop"
$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$Venv = [IO.Path]::GetFullPath((Join-Path $Root $VenvName))
$Expected = [IO.Path]::GetFullPath((Join-Path $Root $VenvName))
if ($Venv -ne $Expected -or !$Venv.StartsWith($Root, [StringComparison]::OrdinalIgnoreCase)) { throw "refusing to remove path outside project: $Venv" }
if (Test-Path -LiteralPath $Venv) {
    Remove-Item -LiteralPath $Venv -Recurse -Force
    Write-Output "removed environment: $Venv"
} else {
    Write-Output "environment not present: $Venv"
}
