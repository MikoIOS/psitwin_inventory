param([switch]$Detener, [switch]$SinNavegador, [switch]$Demo)

$ErrorActionPreference = 'Stop'

if ($Demo) {
    & (Join-Path $PSScriptRoot 'iniciar_forecasting_pruebas.ps1') -Detener:$Detener
    exit $LASTEXITCODE
}

$backendRoot = Split-Path $PSScriptRoot -Parent
$projectRoot = Split-Path $backendRoot -Parent
$frontendRoot = Join-Path $projectRoot 'frontend'
Set-Location -LiteralPath $projectRoot
$runDir = Join-Path $projectRoot 'artifacts\run.local'
$stateFile = Join-Path $runDir 'procesos.json'
New-Item -ItemType Directory -Force -Path $runDir | Out-Null

function Read-ProcessState {
    if (Test-Path -LiteralPath $stateFile) {
        function Expand-Entry($item) {
            foreach ($record in $item) {
                if ($record.id -and $record.started) { $record }
                elseif ($record.value) { Expand-Entry $record.value }
            }
        }
        Expand-Entry (Get-Content -LiteralPath $stateFile -Raw | ConvertFrom-Json)
    }
}

if ($Detener) {
    if (Test-Path -LiteralPath $stateFile) {
        foreach ($entry in @(Read-ProcessState)) {
            $process = Get-Process -Id $entry.id -ErrorAction SilentlyContinue
            if ($process -and $process.StartTime.ToUniversalTime().ToString('o') -eq $entry.started) {
                Stop-Process -Id $process.Id
                Write-Host "Detenido: $($entry.name)"
            }
        }
        Remove-Item -LiteralPath $stateFile
    }
    exit 0
}

function Test-Endpoint([string]$Url) {
    try { return (Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 5).StatusCode -eq 200 }
    catch { return $false }
}

function Wait-Endpoint([string]$Url, $Process, [string]$Name) {
    $deadline = (Get-Date).AddSeconds(60)
    do {
        if (Test-Endpoint $Url) { return }
        $Process.Refresh()
        if ($Process.HasExited) { throw "$Name termino. Revisa $runDir\$Name.err.log" }
        Start-Sleep -Milliseconds 500
    } while ((Get-Date) -lt $deadline)
    throw "$Name no respondio en 60 segundos. Revisa los logs en $runDir"
}

$owned = @()
if (Test-Path -LiteralPath $stateFile) {
    $owned = @(Read-ProcessState)
}
function Save-Process($Process, [string]$Name) {
    $script:owned += [pscustomobject]@{ id = $Process.Id; name = $Name; started = $Process.StartTime.ToUniversalTime().ToString('o') }
    $script:owned | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath $stateFile -Encoding UTF8
}

try {
    $backendReady = Test-Endpoint 'http://127.0.0.1:8000/health'
    $frontendReady = Test-Endpoint 'http://127.0.0.1:5173'
    if (-not $backendReady) {
        $python = $null
        foreach ($candidatePath in @('backend\.venv\Scripts\python.exe', '.venv\Scripts\python.exe', '.runtime.local\python\python.exe')) {
            $candidate = Join-Path $projectRoot $candidatePath
            if (-not (Test-Path -LiteralPath $candidate)) { continue }
            try {
                & $candidate -c 'import uvicorn, fastapi, motor' 2>$null
                if ($LASTEXITCODE -eq 0) { $python = $candidate; break }
            } catch { continue }
        }
        if (-not $python) { throw 'Python o sus dependencias no estan disponibles. Repara .venv e instala requirements.txt.' }

        # Reutiliza servicios locales; inicia contenedores existentes si Docker esta disponible.
        $mongo = Get-Service -Name '*Mongo*' -ErrorAction SilentlyContinue
        foreach ($service in $mongo) {
            if ($service.Status -ne 'Running') {
                try { Start-Service -Name $service.Name }
                catch { Write-Host "No se pudo iniciar $($service.Name); se comprobara la conexion desde el backend." }
            }
        }
        if (Get-Command docker.exe -ErrorAction SilentlyContinue) {
            # Start-Process captura stderr sin convertirlo en una excepcion de PowerShell 5.1.
            $dockerOut = Join-Path $runDir 'docker.out.log'
            $dockerErr = Join-Path $runDir 'docker.err.log'
            $dockerCheck = Start-Process -FilePath (Get-Command docker.exe).Source -ArgumentList @('ps', '-a', '--format', '{{.Names}}') -WindowStyle Hidden -RedirectStandardOutput $dockerOut -RedirectStandardError $dockerErr -PassThru
            if (-not $dockerCheck.WaitForExit(10000)) {
                Stop-Process -Id $dockerCheck.Id -ErrorAction SilentlyContinue
                Write-Host 'Docker no responde; continuando con los servicios locales.'
            } elseif ($dockerCheck.ExitCode -eq 0) {
                $containers = @(Get-Content -LiteralPath $dockerOut)
                foreach ($name in @('psitwin-mongo', 'psitwin-mosquitto')) {
                    if ($containers -contains $name) {
                        $dockerStart = Start-Process -FilePath (Get-Command docker.exe).Source -ArgumentList @('start', $name) -WindowStyle Hidden -RedirectStandardOutput (Join-Path $runDir "$name.out.log") -RedirectStandardError (Join-Path $runDir "$name.err.log") -PassThru
                        if (-not $dockerStart.WaitForExit(10000)) {
                            Stop-Process -Id $dockerStart.Id -ErrorAction SilentlyContinue
                            Write-Host "No se pudo iniciar $name a tiempo; revisa sus logs."
                        }
                    }
                }
            } else {
                Write-Host 'Docker esta apagado; continuando con los servicios locales.'
            }
        }
        Write-Host 'Iniciando backend...'
        $backend = Start-Process -FilePath $python -ArgumentList @('-m', 'app.run', '--host', '127.0.0.1', '--port', '8000') -WorkingDirectory $backendRoot -WindowStyle Hidden -RedirectStandardOutput (Join-Path $runDir 'backend.out.log') -RedirectStandardError (Join-Path $runDir 'backend.err.log') -PassThru
        Save-Process $backend 'backend'
        Wait-Endpoint 'http://127.0.0.1:8000/health' $backend 'backend'
    }
    if (-not $frontendReady) {
        foreach ($entry in @($owned | Where-Object { $_.name -eq 'frontend' })) {
            $previous = Get-Process -Id $entry.id -ErrorAction SilentlyContinue
            if ($previous -and $previous.StartTime.ToUniversalTime().ToString('o') -eq $entry.started) {
                Write-Host 'Reiniciando el frontend anterior que no responde...'
                Stop-Process -Id $previous.Id
                $previous.WaitForExit(5000) | Out-Null
            }
        }
        if (Get-NetTCPConnection -State Listen -LocalPort 5173 -ErrorAction SilentlyContinue) {
            throw 'El puerto 5173 esta ocupado pero no responde. Revisa el proceso existente antes de reiniciar.'
        }
        $node = (Get-Command node.exe -ErrorAction Stop).Source
        $vite = Join-Path $frontendRoot 'node_modules\vite\bin\vite.js'
        if (-not (Test-Path -LiteralPath $vite)) { $vite = Join-Path $projectRoot 'node_modules\vite\bin\vite.js' }
        if (-not (Test-Path -LiteralPath $vite)) { throw 'Faltan dependencias. Ejecuta npm.cmd --prefix frontend ci.' }
        Write-Host 'Compilando frontend...'
        & npm.cmd --prefix $frontendRoot run build
        if ($LASTEXITCODE -ne 0) { throw 'La compilacion del frontend fallo. Revisa los errores anteriores.' }
        Write-Host 'Iniciando frontend...'
        $frontend = Start-Process -FilePath $node -ArgumentList @(('"' + $vite + '"'), 'preview', '--host', '127.0.0.1', '--port', '5173', '--strictPort') -WorkingDirectory $frontendRoot -WindowStyle Hidden -RedirectStandardOutput (Join-Path $runDir 'frontend.out.log') -RedirectStandardError (Join-Path $runDir 'frontend.err.log') -PassThru
        Save-Process $frontend 'frontend'
        Wait-Endpoint 'http://127.0.0.1:5173' $frontend 'frontend'
    }
    Write-Host 'PsiTwin listo: http://localhost:5173'
    Write-Host "Logs: $runDir"
    Write-Host 'Para detener: .\iniciar.cmd -Detener'
    if (-not $SinNavegador) { Start-Process 'http://localhost:5173' }
    Write-Host 'Deja esta terminal abierta mientras usas PsiTwin.'
    $activeIds = @($owned | ForEach-Object {
        $active = Get-Process -Id $_.id -ErrorAction SilentlyContinue
        if ($active -and $active.StartTime.ToUniversalTime().ToString('o') -eq $_.started) { $active.Id }
    })
    if ($activeIds.Count) { Wait-Process -Id $activeIds -ErrorAction SilentlyContinue }
} catch {
    Write-Host "ERROR: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
