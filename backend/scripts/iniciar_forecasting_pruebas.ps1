param([switch]$Detener)
$ErrorActionPreference = 'Stop'
$backendRoot = Split-Path $PSScriptRoot -Parent
$projectRoot = Split-Path $backendRoot -Parent
$frontendRoot = Join-Path $projectRoot 'frontend'
$vite = Join-Path $frontendRoot 'node_modules\vite\bin\vite.js'
if (-not (Test-Path -LiteralPath $vite)) { $vite = Join-Path $projectRoot 'node_modules\vite\bin\vite.js' }
$runDir = Join-Path $projectRoot 'artifacts\forecasting-run.local'
$stateFile = Join-Path $runDir 'procesos.json'
New-Item -ItemType Directory -Force -Path $runDir | Out-Null

function Stop-Owned($entries) {
    foreach ($entry in ($entries | ForEach-Object { $_ })) {
        $process = Get-Process -Id $entry.id -ErrorAction SilentlyContinue
        if ($process -and $process.StartTime.ToUniversalTime().ToString('o') -eq $entry.started) {
            Stop-Process -Id $process.Id
        }
    }
}

if ($Detener) {
    if (Test-Path -LiteralPath $stateFile) {
        Stop-Owned @(Get-Content -LiteralPath $stateFile -Raw | ConvertFrom-Json)
    }
    Write-Host 'Servicios de forecasting de prueba detenidos.'
    exit 0
}

foreach ($port in @(8001, 5174)) {
    if (Get-NetTCPConnection -State Listen -LocalPort $port -ErrorAction SilentlyContinue) {
        throw "Puerto $port ocupado. Si ya iniciaste las pruebas, abre http://127.0.0.1:5174; para reiniciar usa -Detener."
    }
}

$env:MONGODB_DATABASE = 'psitwin_demo10_test'
$env:MQTT_ENABLED = 'false'
$env:CORS_ORIGINS = 'http://127.0.0.1:5174,http://localhost:5174'
$env:VITE_API_URL = '/api/v1'
$env:VITE_PROXY_TARGET = 'http://127.0.0.1:8001'
$env:PYTHONUTF8 = '1'
$python = Join-Path $projectRoot '.venv\Scripts\python.exe'
if (Test-Path -LiteralPath (Join-Path $projectRoot '.venv-forecasting\Scripts\python.exe')) {
    $python = Join-Path $projectRoot '.venv-forecasting\Scripts\python.exe'
}
$owned = @()
try {
    Push-Location -LiteralPath $frontendRoot
    try {
        & npm.cmd run build
        if ($LASTEXITCODE -ne 0) { throw 'Fallo la compilacion de la web.' }
    } finally { Pop-Location }
    $backend = Start-Process -FilePath $python -ArgumentList @('-m', 'uvicorn', 'app.main:app', '--host', '127.0.0.1', '--port', '8001') -WorkingDirectory $backendRoot -WindowStyle Hidden -RedirectStandardOutput (Join-Path $runDir 'backend.out.log') -RedirectStandardError (Join-Path $runDir 'backend.err.log') -PassThru
    $owned += @{ id = $backend.Id; started = $backend.StartTime.ToUniversalTime().ToString('o') }
    $frontend = Start-Process -FilePath (Get-Command node.exe).Source -ArgumentList @(('"' + $vite + '"'), 'preview', '--host', '127.0.0.1', '--port', '5174', '--strictPort') -WorkingDirectory $frontendRoot -WindowStyle Hidden -RedirectStandardOutput (Join-Path $runDir 'frontend.out.log') -RedirectStandardError (Join-Path $runDir 'frontend.err.log') -PassThru
    $owned += @{ id = $frontend.Id; started = $frontend.StartTime.ToUniversalTime().ToString('o') }
    $owned | ConvertTo-Json | Set-Content -LiteralPath $stateFile -Encoding UTF8
    $deadline = (Get-Date).AddSeconds(45)
    do {
        try {
            $health = Invoke-RestMethod 'http://127.0.0.1:8001/health' -TimeoutSec 2
            $web = Invoke-WebRequest 'http://127.0.0.1:5174' -UseBasicParsing -TimeoutSec 2
            if ($health.database_name -eq 'psitwin_demo10_test' -and $web.StatusCode -eq 200) {
                Write-Host 'Pruebas listas: http://127.0.0.1:5174/analisis'
                Write-Host 'Base: psitwin_demo10_test. No se importa ningun CSV al iniciar.'
                Write-Host "Logs: $runDir"
                exit 0
            }
            $lastProbe = "Base recibida: $($health.database_name); estado web: $($web.StatusCode)"
        } catch { $lastProbe = $_.Exception.Message }
        $backend.Refresh(); $frontend.Refresh()
        if ($backend.HasExited -or $frontend.HasExited) { throw "Un servicio termino. Revisa $runDir" }
        Start-Sleep -Milliseconds 500
    } while ((Get-Date) -lt $deadline)
    throw "Los servicios no respondieron a tiempo ($lastProbe). Revisa $runDir"
} catch {
    Stop-Owned $owned
    throw
}
