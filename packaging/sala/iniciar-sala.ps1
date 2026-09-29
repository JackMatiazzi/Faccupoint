[CmdletBinding()]
param([string]$Endereco = 'localhost')
$ErrorActionPreference = 'Stop'
$pastaProjeto = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '../..')).Path
if ($Endereco -ne 'localhost') {
    $ipSala = $null
    if (-not [System.Net.IPAddress]::TryParse($Endereco, [ref]$ipSala) -or $ipSala.AddressFamily -ne 'InterNetwork') {
        throw 'Informe localhost ou o IPv4 da interface local usada na sala.'
    }
    if (-not (Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.IPAddress -eq $Endereco })) {
        throw 'O IP informado nao pertence a este computador.'
    }
}
$env:SALA_BIND = if ($Endereco -eq 'localhost') { '127.0.0.1' } else { $Endereco }
Push-Location $pastaProjeto
try {
    python packaging/sala/preparar.py
    if ($LASTEXITCODE -ne 0) { throw 'Falha ao preparar segredos.' }
    docker compose -f packaging/sala/compose.yaml up -d --build
    if ($LASTEXITCODE -ne 0) { throw 'Falha ao iniciar ambiente Docker.' }
    $env:API_URL = 'http://127.0.0.1:18000'
    $env:ALUNO_PUBLIC_URL = "http://${Endereco}:8081"
    Write-Output "Aluno: $env:ALUNO_PUBLIC_URL"
    Write-Output 'Professor: professor@teste.invalid; PIN local em .local/sala-secrets/admin_pin (inicial; se trocar na interface, use o novo PIN).'
    Start-Process -FilePath (Get-Command python).Source -ArgumentList '-m','professor.main' -WorkingDirectory (Join-Path $pastaProjeto 'frontend') -WindowStyle Hidden
} finally { Pop-Location }
