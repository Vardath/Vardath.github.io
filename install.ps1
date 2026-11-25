$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
  Write-Host 'Node.js LTS is required: https://nodejs.org/en/download' -ForegroundColor Yellow
  exit 1
}
if (-not (Get-Command npm -ErrorAction SilentlyContinue)) { Write-Error 'npm missing'; exit 1 }
if (-not (Get-Command py -ErrorAction SilentlyContinue)) { Write-Error 'Python 3 is required'; exit 1 }
Write-Host 'Installing the ONNX/Transformers.js runtime (one-time network operation)...'
& npm.cmd install --no-fund --no-audit
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Write-Host 'Downloading ONNX coding model (~2 GB; one-time operation)...'
& py -3 .\download_model.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Write-Host 'Installation ready. Start with: py -3 .\start_model.py'
