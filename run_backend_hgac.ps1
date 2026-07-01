$ErrorActionPreference = "Stop"

$repo = Split-Path -Parent $MyInvocation.MyCommand.Path
$localPython = Join-Path $repo ".venv\Scripts\python.exe"
$fallbackPython = Join-Path $repo "..\..\repo_review\HGAC-API\.venv\Scripts\python.exe"

if (Test-Path -LiteralPath $localPython) {
    $previousErrorAction = $ErrorActionPreference
    $ErrorActionPreference = "SilentlyContinue"
    & $localPython -c "import fastapi, uvicorn, dotenv" 2>$null
    $localReady = $LASTEXITCODE -eq 0
    $ErrorActionPreference = $previousErrorAction
}

if ((Test-Path -LiteralPath $localPython) -and $localReady) {
    $python = $localPython
} elseif (Test-Path -LiteralPath $fallbackPython) {
    $python = (Resolve-Path $fallbackPython).Path
} else {
    throw "No se encontro un entorno Python. Cree .venv e instale requirements.txt."
}

Set-Location $repo
Write-Host "Backend HGAC: http://127.0.0.1:8000"
Write-Host "Swagger:      http://127.0.0.1:8000/docs"
Write-Host "Detener:      Ctrl+C"
& $python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
