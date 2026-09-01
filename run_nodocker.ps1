# FaceProof no-Docker launcher: Python backend (in-process blockchain) + prebuilt UI.
$ErrorActionPreference = "Continue"
Set-Location -LiteralPath $PSScriptRoot
$log = Join-Path $PSScriptRoot "run_nodocker.log"
function Say($m){ $m | Tee-Object -FilePath $log -Append }
"START $(Get-Date)" | Set-Content -Path $log

# ---- 1. locate Python (prefer 3.11) ----
$PY = ""
if (Get-Command py -ErrorAction SilentlyContinue) {
  py -3.11 --version 1>$null 2>$null; if ($LASTEXITCODE -eq 0) { $PY = "py -3.11" }
  if (-not $PY) { py -3.10 --version 1>$null 2>$null; if ($LASTEXITCODE -eq 0) { $PY = "py -3.10" } }
  if (-not $PY) { py --version 1>$null 2>$null; if ($LASTEXITCODE -eq 0) { $PY = "py" } }
}
if (-not $PY -and (Get-Command python -ErrorAction SilentlyContinue)) { $PY = "python" }
if (-not $PY) {
  Say "PYTHON_NOT_FOUND"
  Say "Install Python 3.11 from https://www.python.org/downloads/release/python-3119/"
  Say "(tick 'Add python.exe to PATH' during install), then re-run this file."
  exit 1
}
Say "Using Python: $PY"
Invoke-Expression "$PY --version 2>&1" | Tee-Object -FilePath $log -Append

# ---- 2. venv ----
$venv = Join-Path $PSScriptRoot "backend\.venv"
$vpy  = Join-Path $venv "Scripts\python.exe"
if (-not (Test-Path $vpy)) {
  Say "Creating virtual environment (backend\.venv)..."
  Invoke-Expression "$PY -m venv `"$venv`"" 2>&1 | Tee-Object -FilePath $log -Append
}
if (-not (Test-Path $vpy)) { Say "VENV_CREATE_FAILED"; exit 1 }

# ---- 3. dependencies ----
Say "Installing dependencies (first run takes several minutes)..."
& $vpy -m pip install --upgrade pip 2>&1 | Tee-Object -FilePath $log -Append
& $vpy -m pip install -r (Join-Path $PSScriptRoot "backend\requirements.txt") 2>&1 | Tee-Object -FilePath $log -Append
if ($LASTEXITCODE -ne 0) {
  Say "FULL_INSTALL_FAILED -> installing core deps without the face model..."
  & $vpy -m pip install fastapi "uvicorn[standard]" pydantic pydantic-settings python-multipart slowapi httpx beautifulsoup4 numpy Pillow opencv-python-headless SQLAlchemy web3 eth-account eth-tester py-evm 2>&1 | Tee-Object -FilePath $log -Append
  Say "NOTE: InsightFace unavailable -> using the built-in OpenCV face engine (all functions still run)."
}

# ---- 4. demo dataset ----
$env:SEARCH_PROVIDER = "demo"
$env:BLOCKCHAIN_MODE = "memory"
Push-Location (Join-Path $PSScriptRoot "backend")
Say "Generating demo dataset..."
& $vpy -m scripts.make_demo_data 2>&1 | Tee-Object -FilePath $log -Append
Pop-Location

# ---- 5. start backend + web servers (each in its own window) ----
$backendDir = Join-Path $PSScriptRoot "backend"
$dist = Join-Path $PSScriptRoot "frontend\dist"
$beCmd = "`$env:SEARCH_PROVIDER='demo'; `$env:BLOCKCHAIN_MODE='memory'; Set-Location '$backendDir'; & '$vpy' -m uvicorn app.main:app --host 127.0.0.1 --port 8000"
$feCmd = "& '$vpy' -m http.server 5173 --directory '$dist'"
Say "Starting backend (port 8000) and web (port 5173)..."
Start-Process powershell -ArgumentList "-NoExit","-NoProfile","-Command",$beCmd
Start-Process powershell -ArgumentList "-NoExit","-NoProfile","-Command",$feCmd

# ---- 6. wait for API, then open browser ----
$up = $false
for ($i = 0; $i -lt 60; $i++) {
  try { $r = Invoke-WebRequest "http://127.0.0.1:8000/api/health" -UseBasicParsing -TimeoutSec 3
        if ($r.StatusCode -eq 200) { $up = $true; break } } catch {}
  Start-Sleep -Seconds 2
}
if ($up) { Say "API_UP"; Say ("health: " + (Invoke-WebRequest 'http://127.0.0.1:8000/api/health' -UseBasicParsing).Content) }
else     { Say "API_NOT_UP_YET (it may still be starting; check the backend window)" }

Start-Process "http://localhost:5173"
Say "OPENED http://localhost:5173  (API docs: http://localhost:8000/api/docs)"
Say "RESULT: LAUNCHED  (upload subject.jpg from this folder to run a scan)"
