$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
& py -3 .\start_model.py
exit $LASTEXITCODE
