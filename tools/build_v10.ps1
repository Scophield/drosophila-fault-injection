param([Parameter(Mandatory=$true)][string]$BuildDirectory, [string]$SourceFile = 'main_v10_final4.tex', [switch]$Promote)
$ErrorActionPreference = 'Stop'
function Invoke-CheckedNative([string]$Executable, [string[]]$Arguments, [string]$LogPath) {
    $savedPreference = $ErrorActionPreference
    try {
        # TeX emits nonfatal maintenance warnings on stderr even when its exit code is zero.
        $ErrorActionPreference = 'Continue'
        & $Executable @Arguments *> $LogPath
        $nativeExitCode = $LASTEXITCODE
    } finally {
        $ErrorActionPreference = $savedPreference
    }
    if ($nativeExitCode -ne 0) { throw "$Executable failed ($nativeExitCode); see $LogPath" }
}
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$paperRoot = Join-Path $repoRoot 'paper'
$buildPath = [System.IO.Path]::GetFullPath($BuildDirectory)
if (Test-Path -LiteralPath $buildPath) { throw "Choose a new build directory: $buildPath" }
New-Item -ItemType Directory -Path $buildPath | Out-Null
# Build from staged sources so stale paper/main.bbl cannot shadow the new bibliography.
Copy-Item -LiteralPath (Join-Path $paperRoot $SourceFile) -Destination (Join-Path $buildPath 'main.tex')
Copy-Item -LiteralPath (Join-Path $paperRoot 'refs.bib') -Destination $buildPath
Copy-Item -LiteralPath (Join-Path $paperRoot 'sections'), (Join-Path $paperRoot 'figs') -Destination $buildPath -Recurse
Push-Location $buildPath
try {
    $texArguments = @('--disable-installer', '-interaction=nonstopmode', '-halt-on-error', '-file-line-error', "-output-directory=$buildPath", 'main.tex')
    Invoke-CheckedNative 'pdflatex' $texArguments (Join-Path $buildPath 'pass1.txt')
    Invoke-CheckedNative 'bibtex' @((Join-Path $buildPath 'main')) (Join-Path $buildPath 'bibtex.txt')
    Invoke-CheckedNative 'pdflatex' $texArguments (Join-Path $buildPath 'pass2.txt')
    Invoke-CheckedNative 'pdflatex' $texArguments (Join-Path $buildPath 'pass3.txt')
    $logText = Get-Content -LiteralPath (Join-Path $buildPath 'main.log') -Raw
    if ($logText -match 'Citation .+ undefined|Reference .+ undefined|There were undefined|Overfull \\[hv]box|Float too large|Missing character:') {
        throw 'Unresolved reference, overflow or missing glyph: inspect main.log before promoting PDF'
    }
    if ($Promote) {
        if ($SourceFile -ne 'main_v10_final4.tex') { throw 'Only the final four-figure candidate may be promoted; historical named PDFs are protected.' }
        $sourceText = Get-Content -LiteralPath (Join-Path $paperRoot $SourceFile) -Raw
        $sectionText = (Get-ChildItem -LiteralPath (Join-Path $paperRoot 'sections') -Filter 'v10_*.tex' | Get-Content -Raw) -join "`n"
        if (($sourceText + $sectionText) -match 'V10_PENDING') { throw 'Unfinished V10 draft marker; PDF not promoted' }
        Copy-Item -LiteralPath (Join-Path $buildPath 'main.pdf') -Destination (Join-Path $paperRoot 'main.pdf')
        Copy-Item -LiteralPath (Join-Path $buildPath 'main.pdf') -Destination (Join-Path $paperRoot 'fly_connectome_fault_assessment_v10_final.pdf')
        Copy-Item -LiteralPath (Join-Path $paperRoot $SourceFile) -Destination (Join-Path $paperRoot 'main.tex')
        Write-Output "Built and promoted checked V10 source/PDF"
    } else { Write-Output "Built staged draft only: $buildPath\main.pdf" }
} finally {
    Pop-Location
}
