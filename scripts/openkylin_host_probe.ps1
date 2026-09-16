param(
    [string]$Output = "runs/openkylin-validation-20260902/host-probe.json"
)

$ErrorActionPreference = "Continue"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root
$outputPath = Join-Path $root $Output
New-Item -ItemType Directory -Force -Path (Split-Path -Parent $outputPath) | Out-Null

function Get-Tool([string]$Name) {
    $command = Get-Command $Name -ErrorAction SilentlyContinue
    if ($command) { return @{ present = $true; path = $command.Source } }
    return @{ present = $false }
}

$computer = Get-CimInstance Win32_ComputerSystem
$os = Get-CimInstance Win32_OperatingSystem
$cpu = Get-CimInstance Win32_Processor | Select-Object -First 1
$volumes = @(Get-Volume | Where-Object DriveLetter | ForEach-Object {
    @{ drive = "$($_.DriveLetter):"; filesystem = $_.FileSystem; free_gb = [math]::Round($_.SizeRemaining / 1GB, 2); size_gb = [math]::Round($_.Size / 1GB, 2) }
})
$hyperv = $null
try {
    $hyperv = (Get-WindowsOptionalFeature -Online -FeatureName Microsoft-Hyper-V-All -ErrorAction Stop).State
} catch {
    $hyperv = "query_failed: $($_.Exception.Message)"
}
$qemu = Get-Tool "qemu-system-x86_64"
if (-not $qemu.present -and (Test-Path "C:\Program Files\qemu\qemu-system-x86_64.exe")) {
    $qemu = @{ present = $true; path = "C:\Program Files\qemu\qemu-system-x86_64.exe" }
}
$qemuImg = Get-Tool "qemu-img"
if (-not $qemuImg.present -and (Test-Path "C:\Program Files\qemu\qemu-img.exe")) {
    $qemuImg = @{ present = $true; path = "C:\Program Files\qemu\qemu-img.exe" }
}
$payload = [ordered]@{
    collected_at = (Get-Date).ToUniversalTime().ToString("o")
    host = [ordered]@{
        os = $os.Caption
        os_version = $os.Version
        architecture = $env:PROCESSOR_ARCHITECTURE
        computer_name = $env:COMPUTERNAME
        cpu = $cpu.Name
        logical_processors = $cpu.NumberOfLogicalProcessors
        ram_gb = [math]::Round($computer.TotalPhysicalMemory / 1GB, 2)
        virtualization_firmware_enabled = $cpu.VirtualizationFirmwareEnabled
        slat = $cpu.SecondLevelAddressTranslationExtensions
        vmx = $cpu.VMMonitorModeExtensions
        hypervisor_present = (Get-ComputerInfo -Property HyperVisorPresent -ErrorAction SilentlyContinue).HyperVisorPresent
        hyperv_feature = $hyperv
        volumes = $volumes
    }
    tools = [ordered]@{
        qemu = $qemu
        qemu_img = $qemuImg
        virtualbox = Get-Tool "VBoxManage"
        vmware = Get-Tool "vmrun"
        libvirt = Get-Tool "virsh"
        wsl = Get-Tool "wsl"
        docker = Get-Tool "docker"
    }
    network = @(Get-NetAdapter | Where-Object Status -eq "Up" | ForEach-Object {
        @{ name = $_.Name; description = $_.InterfaceDescription; link_speed = "$($_.LinkSpeed)" }
    })
    notes = @(
        "This probe never treats Windows, WSL, Docker, or another Linux distribution as openKylin.",
        "Hyper-V feature status may require an elevated shell; a query failure is recorded verbatim."
    )
}
$payload | ConvertTo-Json -Depth 8 | Tee-Object -FilePath $outputPath
Write-Output "host probe: $outputPath"
