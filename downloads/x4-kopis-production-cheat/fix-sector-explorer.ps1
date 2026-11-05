<#
Optional one-time fix for the third-party Sector Explorer (fs_exp) loose XML script.
Usage: .\\fix-sector-explorer.ps1 -ExtensionsPath 'C:\\Games\\X4 Foundations\\extensions'
Steam/packed CAT DAT installations must be updated by their mod author instead.
#>
param(
  [Parameter(Mandatory = $true)]
  [string]$ExtensionsPath
)
$ErrorActionPreference = 'Stop'
$scriptPath = Join-Path $ExtensionsPath 'fs_exp\\aiscripts\\sectorexplorer.xml'
if (-not (Test-Path -LiteralPath $scriptPath -PathType Leaf)) {
  throw "Sector Explorer loose XML script not found: $scriptPath"
}
$original = [System.IO.File]::ReadAllText($scriptPath)
$old = 'blacklisttype.travel'
$new = 'blacklisttype.sectortravel'
if (-not $original.Contains($old)) {
  Write-Host "No obsolete blacklisttype.travel found; no changes made."
  exit 0
}
$backup = "$scriptPath.vardath-backup"
if (-not (Test-Path -LiteralPath $backup)) {
  Copy-Item -LiteralPath $scriptPath -Destination $backup
}
$fixed = $original.Replace($old, $new)
[System.IO.File]::WriteAllText($scriptPath, $fixed, [System.Text.UTF8Encoding]::new($false))
Write-Host "Updated Sector Explorer blacklist token; original backed up at $backup"
