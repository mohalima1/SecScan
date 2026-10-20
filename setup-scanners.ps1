# Run from normal Windows PowerShell. Installs system prerequisites through WinGet
# and keeps SQLMap/Nikto source plus daemon data in the ignored .tools directory.
[CmdletBinding()]
param([switch]$CheckOnly)

$ErrorActionPreference = 'Stop'
$projectRoot = $PSScriptRoot
$toolRoot = Join-Path $projectRoot '.tools'
$envFile = Join-Path $projectRoot 'backend\.env'

function Find-File([string[]]$Candidates) {
    foreach ($candidate in $Candidates) {
        if ($candidate -and (Test-Path -LiteralPath $candidate -PathType Leaf)) {
            return (Resolve-Path -LiteralPath $candidate).Path
        }
    }
    return $null
}

function Command-Path([string]$Name) {
    $command = Get-Command $Name -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($command) { return $command.Source }
    return $null
}

function Install-Package([string]$Id) {
    Write-Host "Checking/installing $Id ..."
    & $script:winget install --id $Id --exact --source winget --accept-package-agreements --accept-source-agreements
    if ($LASTEXITCODE -ne 0) {
        & $script:winget list --id $Id --exact --source winget --accept-source-agreements
        if ($LASTEXITCODE -ne 0) { throw "WinGet could not install $Id. Review its output above, then rerun setup." }
    }
}

function Install-Source([string]$Repository, [string]$Name, [string]$Entry) {
    $destination = Join-Path $toolRoot $Name
    $existing = Join-Path $destination $Entry
    if (Test-Path -LiteralPath $existing -PathType Leaf) { return $existing }
    if (Test-Path -LiteralPath $destination) {
        throw "Incomplete tool directory: $destination. Rename it before retrying; setup will not overwrite it."
    }
    $headers = @{ 'User-Agent' = 'SecScan-local-setup' }
    # Repositories may rename their default branch; discover it instead of
    # assuming the historical name "master".
    $repoInfo = Invoke-RestMethod -Uri "https://api.github.com/repos/$Repository" -Headers $headers -TimeoutSec 30
    if (-not $repoInfo.default_branch) { throw "GitHub did not report a default branch for $Repository" }
    $branch = [uri]::EscapeDataString([string]$repoInfo.default_branch)
    $commit = (Invoke-RestMethod -Uri "https://api.github.com/repos/$Repository/commits/$branch" -Headers $headers -TimeoutSec 30).sha
    if ($commit -notmatch '^[a-f0-9]{40}$') { throw "Invalid commit metadata for $Repository" }
    $stage = Join-Path $toolRoot ([guid]::NewGuid().ToString())
    New-Item -ItemType Directory -Path $stage | Out-Null
    $archive = Join-Path $stage 'source.zip'
    Write-Host "Downloading $Repository at $commit ..."
    Invoke-WebRequest -Uri "https://github.com/$Repository/archive/$commit.zip" -OutFile $archive -UseBasicParsing -TimeoutSec 300
    Expand-Archive -LiteralPath $archive -DestinationPath (Join-Path $stage 'source')
    $source = @(Get-ChildItem (Join-Path $stage 'source') -Directory)
    if ($source.Count -ne 1 -or -not (Test-Path (Join-Path $source[0].FullName $Entry))) {
        throw "Unexpected archive layout for $Repository; download retained at $stage"
    }
    # This moves only the newly extracted folder inside the validated workspace.
    $sourcePath = $source[0].FullName
    if (-not $sourcePath.StartsWith($toolRoot + '\', [StringComparison]::OrdinalIgnoreCase)) { throw 'Unexpected extraction path.' }
    Move-Item -LiteralPath $sourcePath -Destination $destination
    Remove-Item -LiteralPath $stage -Recurse -Force -ErrorAction SilentlyContinue
    [IO.File]::WriteAllText((Join-Path $destination 'secscan-source-commit.txt'), $commit)
    return (Join-Path $destination $Entry)
}

function Set-Setting([string]$Key, [string]$Value) {
    if ($Value -match "[\r\n']") { throw "Unsupported characters in $Key" }
    $lines = @(Get-Content -LiteralPath $envFile)
    $pattern = '^\s*' + [regex]::Escape($Key) + '\s*='
    $replacement = "$Key='$Value'"
    if (@($lines | Where-Object { $_ -match $pattern }).Count) {
        $lines = @($lines | ForEach-Object { if ($_ -match $pattern) { $replacement } else { $_ } })
    } else { $lines += $replacement }
    [IO.File]::WriteAllLines($envFile, [string[]]$lines, [Text.UTF8Encoding]::new($false))
}

$script:winget = Command-Path 'winget.exe'
if (-not $script:winget) {
    throw 'WinGet is unavailable. Install/update Microsoft App Installer from https://aka.ms/getwinget, open a new PowerShell window, and rerun setup.'
}
if ($CheckOnly) {
    Write-Host "WinGet found: $script:winget"
    Write-Host 'No downloads, configuration changes, or installations performed.'
    exit 0
}

New-Item -ItemType Directory -Path $toolRoot -Force | Out-Null
# The package manager verifies installer hashes. Windows may request elevation.
Install-Package 'Insecure.Nmap'
Install-Package 'StrawberryPerl.StrawberryPerl'
Install-Package 'EclipseAdoptium.Temurin.21.JRE'
Install-Package 'ZAP.ZAP'

$nmap = Find-File @((Command-Path 'nmap.exe'), 'C:\Program Files (x86)\Nmap\nmap.exe', 'C:\Program Files\Nmap\nmap.exe')
$perl = Find-File @((Command-Path 'perl.exe'), 'C:\Strawberry\perl\bin\perl.exe')
$java = Get-ChildItem 'C:\Program Files\Eclipse Adoptium' -Filter java.exe -File -Recurse -ErrorAction SilentlyContinue |
    Where-Object { $_.FullName -match '(jre|jdk)-21[.\-]' } | Sort-Object FullName -Descending | Select-Object -First 1
$zapJar = @('C:\Program Files\ZAP\Zed Attack Proxy', 'C:\Program Files\OWASP\Zed Attack Proxy') |
    ForEach-Object { Get-ChildItem -LiteralPath $_ -Filter 'zap-*.jar' -File -ErrorAction SilentlyContinue } |
    Select-Object -First 1
if (-not $nmap -or -not $perl -or -not $java -or -not $zapJar) {
    throw 'An installed executable could not be located. Open a new terminal, check installer output and install locations, then rerun setup.'
}
$sqlmap = Install-Source 'sqlmapproject/sqlmap' 'sqlmap' 'sqlmap.py'
$niktoScript = Join-Path $projectRoot 'backend\scripts\nikto.pl'
$niktoDestination = Join-Path $toolRoot 'nikto\program\nikto.pl'
if (Test-Path -LiteralPath $niktoScript) {
    New-Item -ItemType Directory -Path (Split-Path $niktoDestination) -Force | Out-Null
    Copy-Item -LiteralPath $niktoScript -Destination $niktoDestination -Force
    $nikto = $niktoDestination
} else {
    $nikto = Install-Source 'sullo/nikto' 'nikto' 'program\nikto.pl'
}

if (-not (Test-Path -LiteralPath $envFile)) {
    Copy-Item -LiteralPath (Join-Path $projectRoot 'backend\.env.example') -Destination $envFile
}
Copy-Item -LiteralPath $envFile -Destination ($envFile + '.' + [guid]::NewGuid().ToString() + '.bak')
$keyLine = Get-Content -LiteralPath $envFile | Where-Object { $_ -match '^\s*ZAP_API_KEY\s*=' } | Select-Object -Last 1
$key = if ($keyLine) { ($keyLine -split '=', 2)[1].Trim().Trim([char]34, [char]39) } else { '' }
if (-not $key) { $key = [guid]::NewGuid().ToString('N') + [guid]::NewGuid().ToString('N') }
if ($key -notmatch '^[A-Za-z0-9_-]+$') { throw 'ZAP_API_KEY must use letters, digits, underscores or hyphens for this daemon launcher.' }
Set-Setting 'NMAP_PATH' ($nmap -replace '\\', '/')
Set-Setting 'PERL_PATH' ($perl -replace '\\', '/')
Set-Setting 'SQLMAP_PATH' ($sqlmap -replace '\\', '/')
Set-Setting 'NIKTO_PATH' ($nikto -replace '\\', '/')
Set-Setting 'ZAP_API' 'http://127.0.0.1:8090'
Set-Setting 'ZAP_API_KEY' $key

$zapProfile = Join-Path $toolRoot 'zap-profile'
New-Item -ItemType Directory -Path $zapProfile -Force | Out-Null
$params = @{ apikey = $key }
$ready = $false
try { $ready = [bool](Invoke-RestMethod 'http://127.0.0.1:8090/JSON/core/view/version/' -Body $params -TimeoutSec 2).version } catch { }
if (-not $ready) {
    if (Get-NetTCPConnection -LocalPort 8090 -State Listen -ErrorAction SilentlyContinue) {
        throw 'Port 8090 is already occupied by another service or ZAP instance. Stop that instance yourself before rerunning setup.'
    }
    Write-Host 'Starting the dedicated local ZAP daemon ...'
    $arguments = @('-jar', ('"' + $zapJar.FullName + '"'), '-daemon', '-host', '127.0.0.1', '-port', '8090', '-dir', ('"' + $zapProfile + '"'), '-config', ('api.key=' + $key))
    Start-Process -FilePath $java.FullName -ArgumentList $arguments -WorkingDirectory $zapJar.DirectoryName -WindowStyle Hidden -RedirectStandardOutput (Join-Path $toolRoot 'zap.stdout.log') -RedirectStandardError (Join-Path $toolRoot 'zap.stderr.log') | Out-Null
    for ($attempt = 0; $attempt -lt 30; $attempt++) {
        Start-Sleep -Seconds 2
        try { $ready = [bool](Invoke-RestMethod 'http://127.0.0.1:8090/JSON/core/view/version/' -Body $params -TimeoutSec 2).version } catch { }
        if ($ready) { break }
    }
}
if (-not $ready) { throw 'ZAP did not become ready. Inspect .tools/zap.stderr.log and .tools/zap-profile/zap.log.' }
Write-Host 'Scanner paths saved and ZAP is responding. No scan was started.'
Write-Host 'Restart both SecScan servers using run.cmd, then select Check tools again.'
