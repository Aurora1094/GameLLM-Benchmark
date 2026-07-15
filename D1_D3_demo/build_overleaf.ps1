param(
    [switch]$SkipPdf
)

$ErrorActionPreference = "Stop"

$DemoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Split-Path -Parent $DemoRoot
$SourceTex = Join-Path $DemoRoot "docs\GameBench_D1_D3.tex"
$GeneratedDir = Join-Path $DemoRoot "results\generated"
$LiveDir = Join-Path $DemoRoot "results\live"
$CalibrationDir = Join-Path $DemoRoot "results"
$RunsRoot = Join-Path $DemoRoot "runs"
$ReportConfigPath = Join-Path $DemoRoot "report_config.json"
$BundleParent = Join-Path $DemoRoot "build\overleaf"
$BundleRoot = Join-Path $BundleParent "GameBench_D1_D3_Overleaf"
$VerifyRoot = Join-Path $DemoRoot "build\overleaf_verify"
$ZipPath = Join-Path $RepoRoot "GameBench_D1_D3_Overleaf.zip"
$PdfPath = Join-Path $RepoRoot "GameBench_D1_D3.pdf"
$TectonicExe = Join-Path $DemoRoot ".tools\tectonic-0.16.9\tectonic.exe"
$Utf8NoBom = New-Object System.Text.UTF8Encoding($false)

if (-not $SkipPdf) {
    & (Join-Path $DemoRoot "build_pdf.ps1") -SkipDemo
    if ($LASTEXITCODE -ne 0) {
        throw "PDF build failed; Overleaf packaging was stopped."
    }
}

foreach ($required in @($SourceTex, $GeneratedDir, $LiveDir, $ReportConfigPath, $PdfPath, $TectonicExe)) {
    if (-not (Test-Path -LiteralPath $required)) {
        throw "Missing Overleaf source dependency: $required"
    }
}

$resolvedDemo = [System.IO.Path]::GetFullPath($DemoRoot)
foreach ($target in @($BundleRoot, $VerifyRoot)) {
    $resolvedTarget = [System.IO.Path]::GetFullPath($target)
    if (-not $resolvedTarget.StartsWith($resolvedDemo, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Unsafe build cleanup path: $resolvedTarget"
    }
    if (Test-Path -LiteralPath $target) {
        Remove-Item -LiteralPath $target -Recurse -Force
    }
}
if (Test-Path -LiteralPath $ZipPath) {
    Remove-Item -LiteralPath $ZipPath -Force
}

New-Item -ItemType Directory -Force $BundleRoot | Out-Null
New-Item -ItemType Directory -Force (Join-Path $BundleRoot "generated") | Out-Null
New-Item -ItemType Directory -Force (Join-Path $BundleRoot "data\calibration") | Out-Null
New-Item -ItemType Directory -Force (Join-Path $BundleRoot "data\live") | Out-Null
New-Item -ItemType Directory -Force (Join-Path $BundleRoot "data\runs") | Out-Null

$mainTex = [System.IO.File]::ReadAllText($SourceTex, [System.Text.Encoding]::UTF8)
$mainTex = $mainTex.Replace("../results/generated/", "generated/")
[System.IO.File]::WriteAllText((Join-Path $BundleRoot "main.tex"), $mainTex, $Utf8NoBom)

Copy-Item -Path (Join-Path $GeneratedDir "*.tex") -Destination (Join-Path $BundleRoot "generated") -Force
Copy-Item -LiteralPath (Join-Path $LiveDir "live_summary.json") -Destination (Join-Path $BundleRoot "data\live") -Force
Copy-Item -LiteralPath (Join-Path $LiveDir "live_results.csv") -Destination (Join-Path $BundleRoot "data\live") -Force
Copy-Item -LiteralPath (Join-Path $CalibrationDir "summary.json") -Destination (Join-Path $BundleRoot "data\calibration") -Force
Copy-Item -LiteralPath (Join-Path $CalibrationDir "d1_results.csv") -Destination (Join-Path $BundleRoot "data\calibration") -Force
Copy-Item -LiteralPath (Join-Path $CalibrationDir "d3_results.csv") -Destination (Join-Path $BundleRoot "data\calibration") -Force
Copy-Item -LiteralPath $ReportConfigPath -Destination (Join-Path $BundleRoot "data") -Force
Copy-Item -LiteralPath $PdfPath -Destination (Join-Path $BundleRoot "compiled_report.pdf") -Force

$config = Get-Content -Raw -Encoding utf8 $ReportConfigPath | ConvertFrom-Json
$runIndex = 0
foreach ($runId in $config.run_ids) {
    $runIndex += 1
    $sourceRun = Join-Path $RunsRoot $runId
    $targetRun = Join-Path $BundleRoot ("data\runs\R" + $runIndex)
    New-Item -ItemType Directory -Force $targetRun | Out-Null
    foreach ($relativePath in @(
        "summary.json",
        "manifest.json",
        "prompts\pong.txt",
        "scores\d1.json",
        "scores\d3.json"
    )) {
        $sourcePath = Join-Path $sourceRun $relativePath
        if (-not (Test-Path -LiteralPath $sourcePath)) {
            throw "Missing live-run artifact for Overleaf package: $sourcePath"
        }
        $targetSubdir = Split-Path -Parent (Join-Path $targetRun $relativePath)
        New-Item -ItemType Directory -Force $targetSubdir | Out-Null
        Copy-Item -LiteralPath $sourcePath -Destination (Join-Path $targetRun $relativePath) -Force
    }
    $generatedCode = Get-ChildItem -LiteralPath (Join-Path $sourceRun "generated") -Filter "*.py" -File | Select-Object -First 1
    if (-not $generatedCode) {
        throw "Missing generated code for Overleaf package: $runId"
    }
    Copy-Item -LiteralPath $generatedCode.FullName -Destination (Join-Path $targetRun "generated_pong.py") -Force
}

$readme = @"
# GameBench D1/D3 Overleaf package

1. Upload this ZIP as a new Overleaf project.
2. Set the compiler to XeLaTeX.
3. Set `main.tex` as the main document and compile.

The package is self-contained. It uses TeX Live's Fandol CJK fonts and includes the generated
LaTeX tables, aggregate CSV/JSON data, audited per-run summaries, D1/D3 score files, prompts,
and generated Python code. `compiled_report.pdf` is the locally verified reference rendering.

The AWS credentials used for model calls are not included.
"@
[System.IO.File]::WriteAllText((Join-Path $BundleRoot "README.md"), $readme, $Utf8NoBom)

$artifactIndex = @()
Get-ChildItem -LiteralPath $BundleRoot -Recurse -File | Sort-Object FullName | ForEach-Object {
    $relative = $_.FullName.Substring($BundleRoot.Length + 1).Replace("\", "/")
    $artifactIndex += [pscustomobject]@{
        path = $relative
        size_bytes = $_.Length
        sha256 = (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
    }
}
$bundleManifest = [pscustomobject]@{
    format_version = 1
    main_document = "main.tex"
    compiler = "XeLaTeX"
    generated_at_utc = [DateTime]::UtcNow.ToString("o")
    artifact_index = $artifactIndex
}
[System.IO.File]::WriteAllText(
    (Join-Path $BundleRoot "MANIFEST.json"),
    ($bundleManifest | ConvertTo-Json -Depth 10) + [Environment]::NewLine,
    $Utf8NoBom
)

New-Item -ItemType Directory -Force $VerifyRoot | Out-Null
Copy-Item -Path (Join-Path $BundleRoot "*") -Destination $VerifyRoot -Recurse -Force
New-Item -ItemType Directory -Force (Join-Path $VerifyRoot "build") | Out-Null
Push-Location $VerifyRoot
try {
    & $TectonicExe -X compile --reruns 2 --keep-logs --outdir (Join-Path $VerifyRoot "build") "main.tex"
    if ($LASTEXITCODE -ne 0) {
        throw "Independent Overleaf-package compilation failed."
    }
}
finally {
    Pop-Location
}

Add-Type -AssemblyName System.IO.Compression
Add-Type -AssemblyName System.IO.Compression.FileSystem
$zipStream = [System.IO.File]::Open($ZipPath, [System.IO.FileMode]::CreateNew)
try {
    $zipArchive = New-Object System.IO.Compression.ZipArchive(
        $zipStream,
        [System.IO.Compression.ZipArchiveMode]::Create,
        $false
    )
    try {
        Get-ChildItem -LiteralPath $BundleRoot -Recurse -File | Sort-Object FullName | ForEach-Object {
            $entryName = $_.FullName.Substring($BundleRoot.Length + 1).Replace("\", "/")
            $entry = $zipArchive.CreateEntry($entryName, [System.IO.Compression.CompressionLevel]::Optimal)
            $entryStream = $entry.Open()
            $fileStream = [System.IO.File]::OpenRead($_.FullName)
            try {
                $fileStream.CopyTo($entryStream)
            }
            finally {
                $fileStream.Dispose()
                $entryStream.Dispose()
            }
        }
    }
    finally {
        $zipArchive.Dispose()
    }
}
finally {
    $zipStream.Dispose()
}
Write-Host "Built: $ZipPath"
