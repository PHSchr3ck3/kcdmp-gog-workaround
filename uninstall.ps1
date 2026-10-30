<#
.SYNOPSIS
    Removes the GOG entry that install.ps1 added to builds.json.

.DESCRIPTION
    Restores builds.json from builds.json.kcdmp-gog.bak when that backup exists.
    Without a backup it removes every build whose store is "gog" and leaves the
    three official builds alone. KcdMp_client.dll is never touched by install or
    uninstall.
#>
[CmdletBinding()]
param(
    [string]$ClientDir = ""
)

$ErrorActionPreference = 'Stop'

if ($ClientDir -eq "") {
    if (Test-Path -LiteralPath (Join-Path $PSScriptRoot 'builds.json')) { $ClientDir = $PSScriptRoot }
    elseif (Test-Path -LiteralPath (Join-Path (Get-Location).Path 'builds.json')) { $ClientDir = (Get-Location).Path }
    else { $ClientDir = $PSScriptRoot }
}

$ClientDir = (Resolve-Path -LiteralPath $ClientDir).Path
$builds = Join-Path $ClientDir 'builds.json'
$backup = Join-Path $ClientDir 'builds.json.kcdmp-gog.bak'

if (-not (Test-Path -LiteralPath $builds)) { Write-Host "ERROR: builds.json not found in $ClientDir" -ForegroundColor Red; exit 1 }

if (Test-Path -LiteralPath $backup) {
    Copy-Item -LiteralPath $backup -Destination $builds -Force
    Remove-Item -LiteralPath $backup -Force
    Write-Host "Restored builds.json from builds.json.kcdmp-gog.bak and removed the backup." -ForegroundColor Green
} else {
    $json = Get-Content -LiteralPath $builds -Raw | ConvertFrom-Json
    $before = @($json.builds).Count
    $json.builds = @($json.builds | Where-Object { $_.store -ne 'gog' })
    $after = @($json.builds).Count
    $text = $json | ConvertTo-Json -Depth 32
    [IO.File]::WriteAllText($builds, $text, (New-Object Text.UTF8Encoding($false)))
    Write-Host "No backup found; removed $($before - $after) gog entry/entries from builds.json." -ForegroundColor Yellow
}

$check = Get-Content -LiteralPath $builds -Raw | ConvertFrom-Json
Write-Host ("builds now: " + (($check.builds | ForEach-Object { $_.id }) -join ', '))
