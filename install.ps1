<#
.SYNOPSIS
    Adds the GOG build of Kingdom Come: Deliverance II 1.5.x to KCD:MP 0.48.1.

.DESCRIPTION
    KCD:MP 0.48.1 knows three game builds (Epic, Microsoft Store, Steam).  This script
    appends a fourth entry, gog-1.5.6-c59754b9, to builds.json next to KcdMp_client.dll.
    The build gate of the client and the launcher's check both read that file, so no
    binary is modified: KcdMp_client.dll stays byte-for-byte the released file.

    The entry holds 277 anchors derived from the GOG WHGame.dll (RTTI vtables, vtable
    slots, PE exports, the gEnv global).  The 247 anchors that the original tool found
    by byte pattern cannot be derived and stay unresolved; the client logs each one and
    turns the matching feature off.  See README.de.md and docs/TECHNICAL.de.md.

    Start KcdMp_launcher.exe as administrator: in the tested environment the game only
    got past its input module (CryInput.dll) when the launcher ran elevated.

.PARAMETER ClientDir
    Folder with KcdMp_launcher.exe, KcdMp_client.dll and builds.json. Defaults to the
    folder of this script, or to the current folder when that holds KcdMp_client.dll.

.PARAMETER GameDir
    Optional: after installing, run the launcher's --check-game against this folder.

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File .\install.ps1 -ClientDir "D:\download\KcdMp-0.48.0-win-x64"
#>
[CmdletBinding()]
param(
    [string]$ClientDir = "",
    [string]$GameDir = ""
)

$ErrorActionPreference = 'Stop'

if ($ClientDir -eq "") {
    if (Test-Path -LiteralPath (Join-Path $PSScriptRoot 'KcdMp_client.dll')) { $ClientDir = $PSScriptRoot }
    elseif (Test-Path -LiteralPath (Join-Path (Get-Location).Path 'KcdMp_client.dll')) { $ClientDir = (Get-Location).Path }
    else { $ClientDir = $PSScriptRoot }
}

$SrcName    = 'KcdMp_client.dll'
$SrcSha256  = 'AD44B2A081470563C9CE9885BACC008EB4AC0F12B239221DD47C8A383AC6653B'
$SrcLength  = 15625152
$EntryFile  = 'gog-1.5.6-c59754b9.json'
$BuildsName = 'builds.json'
$BackupName = 'builds.json.kcdmp-gog.bak'

function Stop-Install([string]$Message) {
    Write-Host "ERROR: $Message" -ForegroundColor Red
    exit 1
}

$ClientDir = (Resolve-Path -LiteralPath $ClientDir).Path
$dll     = Join-Path $ClientDir $SrcName
$builds  = Join-Path $ClientDir $BuildsName
$entry   = Join-Path $PSScriptRoot $EntryFile
if (-not (Test-Path -LiteralPath $entry)) { $entry = Join-Path $ClientDir $EntryFile }
$backup  = Join-Path $ClientDir $BackupName
$launcher = Join-Path $ClientDir 'KcdMp_launcher.exe'

foreach ($p in @($dll, $builds, $entry)) {
    if (-not (Test-Path -LiteralPath $p)) { Stop-Install "not found: $p" }
}

$len = (Get-Item -LiteralPath $dll).Length
if ($len -ne $SrcLength) { Stop-Install "$SrcName has $len bytes, expected $SrcLength (KCD:MP 0.48.1)." }
$hash = (Get-FileHash -LiteralPath $dll -Algorithm SHA256).Hash
if ($hash -ne $SrcSha256) {
    Stop-Install ("$SrcName is not the 0.48.1 file (SHA-256 $hash).`n" +
                  "This entry was derived for exactly that file. If the launcher updated KCD:MP, do not use this fix.")
}

$buildsJson = Get-Content -LiteralPath $builds -Raw | ConvertFrom-Json
$newEntry   = Get-Content -LiteralPath $entry -Raw | ConvertFrom-Json

if (-not ($newEntry.PSObject.Properties.Name -contains 'resolved')) { Stop-Install "$EntryFile has no resolved table." }
$anchorCount = @($newEntry.resolved.PSObject.Properties).Count
if ($anchorCount -lt 270) { Stop-Install "$EntryFile holds only $anchorCount anchors; the file is incomplete." }

if (-not (Test-Path -LiteralPath $backup)) {
    Copy-Item -LiteralPath $builds -Destination $backup
    Write-Host "Backup: $BackupName"
}

# Drop an older gog-* entry, keep the three official ones.
$kept = @($buildsJson.builds | Where-Object { $_.store -ne 'gog' })
$buildsJson.builds = @($kept) + @($newEntry)

$tmp = "$builds.tmp"
$text = $buildsJson | ConvertTo-Json -Depth 32
[IO.File]::WriteAllText($tmp, $text, (New-Object Text.UTF8Encoding($false)))
Copy-Item -LiteralPath $tmp -Destination $builds -Force
Remove-Item -LiteralPath $tmp -Force

# Re-read: the file must parse and carry the entry.
$check = Get-Content -LiteralPath $builds -Raw | ConvertFrom-Json
$got = @($check.builds | Where-Object { $_.id -eq 'gog-1.5.6-c59754b9' })
if ($got.Count -ne 1) { Stop-Install "builds.json does not hold the entry after writing." }
Write-Host "Installed gog-1.5.6-c59754b9 with $anchorCount anchors into $BuildsName." -ForegroundColor Green

if ($GameDir -ne "" -and (Test-Path -LiteralPath $launcher)) {
    & $launcher --check-game --game $GameDir
    Write-Host "launcher --check-game exit code: $LASTEXITCODE (0 = supported)"
}

Write-Host ""
Write-Host "Start KcdMp_launcher.exe as administrator. The client reads builds.json from its own folder;"
Write-Host "the log line to look for is: build gate: build gog-1.5.6-c59754b9 (supported), $anchorCount anchors"
