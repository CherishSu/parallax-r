# Run from any directory. No installation or API key required.
$ErrorActionPreference = 'Stop'
Push-Location $PSScriptRoot
try {
    python run.py --mode demo --ledger --stress
    if ($LASTEXITCODE -ne 0) { throw 'Demo failed. Read the error above.' }
    Write-Host 'Open output/demo/report.html in a browser to follow the six steps.'
} finally { Pop-Location }
