param(
    [string]$Vmx = 'D:\openKylin-VM\openKylin.vmx',
    [string]$Vmrun = 'E:\VMware\vmrun.exe',
    [string]$User = 'Cisyam',
    [string]$Key = "$env:USERPROFILE\.ssh\openkylin_vm_ed25519"
)

$ErrorActionPreference = 'Stop'

if (-not (Test-Path -LiteralPath $Vmrun)) {
    throw "vmrun not found: $Vmrun"
}
if (-not (Test-Path -LiteralPath $Vmx)) {
    throw "VMX not found: $Vmx"
}
if (-not (Test-Path -LiteralPath $Key)) {
    throw "SSH key not found: $Key"
}

$ip = (& $Vmrun -T ws getGuestIPAddress $Vmx -wait 2>&1 | Select-Object -Last 1).ToString().Trim()
if (-not $ip -or $ip -match '^Error:') {
    throw "Could not get guest IP. vmrun output: $ip"
}

Write-Host "Guest IP: $ip"

$openPorts = @()
foreach ($port in @(22, 2222)) {
    $ok = (Test-NetConnection -ComputerName $ip -Port $port -InformationLevel Quiet)
    Write-Host "Port $port open: $ok"
    if ($ok) {
        $openPorts += $port
    }
}

if ($openPorts.Count -eq 0) {
    throw "Neither port 22 nor 2222 is reachable on $ip"
}

$portArg = @()
if ($openPorts[0] -ne 22) {
    $portArg = @('-p', [string]$openPorts[0])
}

& ssh @portArg -i $Key -o IdentitiesOnly=yes -o StrictHostKeyChecking=accept-new "$User@$ip" "whoami; hostname; cat /etc/os-release | head -n 5; uname -a; python3 --version || true"
