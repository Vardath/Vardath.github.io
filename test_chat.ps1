$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
& py -3 .\chat.py 'Write a Python function to calculate prime numbers.'
exit $LASTEXITCODE
