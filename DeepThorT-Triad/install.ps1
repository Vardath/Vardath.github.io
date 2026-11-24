$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
& py -3 .\download_model.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Write-Host 'Triad installed. Start via py -3 .\desktop_launcher.py'
