param(
    [string]$VmDir = "runs/openkylin-validation-20260902/qemu-x86_64",
    [ValidateSet("whpx", "tcg")][string]$Accel = "whpx",
    [int]$Seconds = 60
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root
$vmPath = Join-Path $root $VmDir
$qemu = "C:\Program Files\qemu\qemu-system-x86_64.exe"
if (-not (Test-Path $qemu)) { $qemu = (Get-Command qemu-system-x86_64 -ErrorAction SilentlyContinue).Source }
$disk = Join-Path $vmPath "openkylin.qcow2"
$mediaPath = Join-Path $root "runs/openkylin-validation-20260902/media"
$iso = Join-Path $mediaPath "openKylin-Desktop-V2.0-SP2-20260813-x86_64.iso"
if (-not $qemu -or -not (Test-Path $qemu)) { throw "qemu-system-x86_64.exe not found" }
if (-not (Test-Path $disk)) { throw "qcow2 disk not found: $disk" }
if (-not (Test-Path $iso)) { throw "ISO not found: $iso" }
$linkRoot = "C:\kmb-openkylin-validation"
$vmLink = Join-Path $linkRoot "vm"
$mediaLink = Join-Path $linkRoot "media"
New-Item -ItemType Directory -Force -Path $linkRoot | Out-Null
foreach ($link in @(@($vmLink, $vmPath), @($mediaLink, $mediaPath))) {
    if (-not (Test-Path $link[0])) { New-Item -ItemType Junction -Path $link[0] -Target $link[1] | Out-Null }
    if (-not (Test-Path $link[0])) { throw "Failed to create ASCII junction: $($link[0])" }
}
$asciiDisk = Join-Path $vmLink "openkylin.qcow2"
$asciiIso = Join-Path $mediaLink "openKylin-Desktop-V2.0-SP2-20260813-x86_64.iso"
$serial = Join-Path $vmLink "boot-$Accel.serial.log"
$stderr = Join-Path $vmPath "boot-$Accel.stderr.log"
$args = @("-name", "openkylin-validation", "-machine", "q35", "-m", "4096", "-smp", "4", "-accel", $Accel, "-drive", "file=$asciiDisk,if=virtio,format=qcow2", "-cdrom", $asciiIso, "-boot", "order=d", "-nic", "user,model=virtio-net-pci", "-serial", "file:$serial", "-display", "none", "-no-reboot")
$started = Get-Date
$psi = [System.Diagnostics.ProcessStartInfo]::new()
$psi.FileName = $qemu
$psi.UseShellExecute = $false
$psi.RedirectStandardError = $true
$psi.Arguments = (($args | ForEach-Object { '"' + $_.Replace('"', '\"') + '"' }) -join ' ')
$process = [System.Diagnostics.Process]::new()
$process.StartInfo = $psi
[void]$process.Start()
$stderrText = $process.StandardError.ReadToEndAsync()
$exited = $process.WaitForExit($Seconds * 1000)
$timedOut = -not $exited
if ($timedOut) { Stop-Process -Id $process.Id -Force -ErrorAction SilentlyContinue; $code = 124 } else { $code = $process.ExitCode }
$stderrText.Result | Set-Content -Path $stderr -Encoding UTF8
$record = [ordered]@{
    started_at = $started.ToUniversalTime().ToString("o")
    finished_at = (Get-Date).ToUniversalTime().ToString("o")
    qemu = $qemu
    accelerator = $Accel
    timeout_seconds = $Seconds
    timed_out = $timedOut
    exit_code = $code
    qemu_arguments = $args
    ascii_junction_root = $linkRoot
    serial_log = $serial
    stderr_log = $stderr
}
$record | ConvertTo-Json | Set-Content -Path (Join-Path $vmPath "boot-$Accel.metadata.json") -Encoding UTF8
Write-Output ($record | ConvertTo-Json)
exit $code
