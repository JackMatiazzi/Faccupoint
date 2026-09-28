[CmdletBinding()]
param([switch]$Aplicar)
$ErrorActionPreference = 'Stop'
$pastaProjeto = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '../..')).Path
$pastaBackup = Join-Path $pastaProjeto '.local/firewall'
$pythonProjeto = (Get-Command python -ErrorAction Stop).Source
$regrasPython = @(Get-NetFirewallRule -Enabled True -Direction Inbound -Action Allow | Where-Object { $_.DisplayName -match '^python(?:\.exe)?$' } | Where-Object {
    $app = $_ | Get-NetFirewallApplicationFilter
    $portas = $_ | Get-NetFirewallPortFilter
    $app.Program -ieq $pythonProjeto -and $portas.LocalPort -eq 'Any'
})
Write-Output 'Plano: bloquear SMB (445) no perfil publico; desabilitar permissoes amplas deste Python; permitir HTTP 8081 apenas na sub-rede local.'
$regrasPython | Select-Object Name, DisplayName, Profile
if (-not $Aplicar) { Write-Output 'Somente consulta. Execute com -Aplicar em PowerShell administrador.'; return }
$admin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $admin) { throw 'Aplicacao exige PowerShell executado como administrador. Nenhuma regra foi alterada.' }
New-Item -ItemType Directory -Path $pastaBackup -Force | Out-Null
$arquivoBackup = Join-Path $pastaBackup ('regras-' + (Get-Date -Format 'yyyyMMdd-HHmmss') + '.json')
$regrasPython | Select-Object Name, Enabled, Profile | ConvertTo-Json | Set-Content -LiteralPath $arquivoBackup -Encoding UTF8
if (-not (Get-NetFirewallRule -Name 'FaccuPoint-Sala-Web' -ErrorAction SilentlyContinue)) {
    New-NetFirewallRule -Name 'FaccuPoint-Sala-Web' -DisplayName 'FaccuPoint sala web local' -Direction Inbound -Action Allow -Protocol TCP -LocalPort 8081 -RemoteAddress LocalSubnet -Profile Private,Public | Out-Null
}
if (-not (Get-NetFirewallRule -Name 'FaccuPoint-Sala-Bloquear-SMB-Publico' -ErrorAction SilentlyContinue)) {
    New-NetFirewallRule -Name 'FaccuPoint-Sala-Bloquear-SMB-Publico' -DisplayName 'FaccuPoint bloquear SMB em rede publica' -Direction Inbound -Action Block -Protocol TCP -LocalPort 445 -Profile Public | Out-Null
}
foreach ($regra in $regrasPython) { Disable-NetFirewallRule -Name $regra.Name | Out-Null }
Write-Output "Aplicado. Registro das regras anteriores: $arquivoBackup"
