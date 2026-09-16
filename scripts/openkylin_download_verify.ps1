param(
    [string]$Url = "https://mirror.nju.edu.cn/openkylin-cdimage/2.0-SP2/openKylin-Desktop-V2.0-SP2-20260813-x86_64.iso",
    [string]$Output = "runs/openkylin-validation-20260902/media/openKylin-Desktop-V2.0-SP2-20260813-x86_64.iso",
    [string]$ExpectedMd5 = "",
    [long]$ExpectedBytes = 8930932736
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root
$outputPath = Join-Path $root $Output
$recordPath = "$outputPath.metadata.json"
New-Item -ItemType Directory -Force -Path (Split-Path -Parent $outputPath) | Out-Null

if (-not (Test-Path $outputPath)) {
    & curl.exe -L --fail --retry 3 --retry-delay 5 -C - -o $outputPath $Url
    if ($LASTEXITCODE -ne 0) { throw "curl failed with exit code $LASTEXITCODE" }
}
$item = Get-Item $outputPath
$sha256 = (Get-FileHash -Algorithm SHA256 -Path $outputPath).Hash.ToLowerInvariant()
$md5 = (Get-FileHash -Algorithm MD5 -Path $outputPath).Hash.ToLowerInvariant()
$record = [ordered]@{
    recorded_at = (Get-Date).ToUniversalTime().ToString("o")
    source_url = $Url
    file = $outputPath
    version = "openKylin 2.0 SP2 (20260813)"
    architecture = "x86_64"
    size_bytes = $item.Length
    expected_size_bytes = $ExpectedBytes
    size_ok = ($ExpectedBytes -le 0 -or $item.Length -eq $ExpectedBytes)
    sha256 = $sha256
    md5 = $md5
    expected_md5 = $ExpectedMd5
    md5_ok = ([string]::IsNullOrWhiteSpace($ExpectedMd5) -or $md5 -eq $ExpectedMd5.ToLowerInvariant())
    official_md5_page = "https://www.openkylin.top/md5.html"
    gpg = [ordered]@{
        status = "not_available"
        reason = "Official download page exposes MD5 values but no detached GPG signature URL for this ISO."
    }
}
$record | ConvertTo-Json -Depth 6 | Tee-Object -FilePath $recordPath
if (-not $record.size_ok -or -not $record.md5_ok) { exit 2 }
Write-Output "image verified: $outputPath"
