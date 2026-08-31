[CmdletBinding()]
param(
    [string]$Output = "../CRE_Expected_Loss_Model_Design.docx"
)

$ErrorActionPreference = "Stop"
$Pandoc = Get-Command pandoc -ErrorAction SilentlyContinue

if (-not $Pandoc) {
    throw "Pandoc is required but was not found. Install Pandoc, then run this script again."
}

$ModelDesignDirectory = Split-Path -Parent $MyInvocation.MyCommand.Path
Push-Location $ModelDesignDirectory
try {
    & $Pandoc.Source --defaults pandoc.yaml --output $Output content.md
    if ($LASTEXITCODE -ne 0) {
        throw "Pandoc failed with exit code $LASTEXITCODE."
    }
    Write-Output (Resolve-Path $Output)
}
finally {
    Pop-Location
}

