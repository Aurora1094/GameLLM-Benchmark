param(
    [switch]$SkipDemo
)

$ErrorActionPreference = "Stop"

$DemoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Split-Path -Parent $DemoRoot
$TectonicVersion = "0.16.9"
$TectonicArchiveName = "tectonic-$TectonicVersion-x86_64-pc-windows-msvc.zip"
$TectonicUrl = "https://github.com/tectonic-typesetting/tectonic/releases/download/tectonic%40$TectonicVersion/$TectonicArchiveName"
$ExpectedSha256 = "131A24604785A9600989A3D91225F597DF52AC06F00AEFFE86FD529F99EE5CDD"
$DownloadsDir = Join-Path $DemoRoot ".tools\downloads"
$ArchivePath = Join-Path $DownloadsDir $TectonicArchiveName
$TectonicDir = Join-Path $DemoRoot ".tools\tectonic-$TectonicVersion"
$TectonicExe = Join-Path $TectonicDir "tectonic.exe"
$BuildDir = Join-Path $DemoRoot "build"
$SummaryPath = Join-Path $DemoRoot "results\summary.json"
$ManifestPath = Join-Path $DemoRoot "results\manifest.json"
$ReportConfigPath = Join-Path $DemoRoot "report_config.json"
$LiveSummaryPath = Join-Path $DemoRoot "results\live\live_summary.json"
$DocumentName = "GameBench_D1_D3"

if (-not (Test-Path -LiteralPath $TectonicExe)) {
    New-Item -ItemType Directory -Force $DownloadsDir | Out-Null
    if (-not (Test-Path -LiteralPath $ArchivePath)) {
        Write-Host "Downloading Tectonic $TectonicVersion..."
        Invoke-WebRequest -Uri $TectonicUrl -OutFile $ArchivePath
    }

    $ActualSha256 = (Get-FileHash -LiteralPath $ArchivePath -Algorithm SHA256).Hash
    if ($ActualSha256 -ne $ExpectedSha256) {
        throw "Tectonic archive SHA256 mismatch. Expected $ExpectedSha256, got $ActualSha256."
    }

    New-Item -ItemType Directory -Force $TectonicDir | Out-Null
    Expand-Archive -LiteralPath $ArchivePath -DestinationPath $TectonicDir -Force
}

if (-not (Test-Path -LiteralPath $ReportConfigPath)) {
    throw "Missing live report configuration: $ReportConfigPath"
}
Push-Location $RepoRoot
try {
    & python "D1_D3_demo\aggregate_live_runs.py" --config "D1_D3_demo\report_config.json"
    if ($LASTEXITCODE -ne 0) {
        throw "Live-run aggregation failed; PDF compilation was stopped."
    }
}
finally {
    Pop-Location
}
if (-not (Test-Path -LiteralPath $LiveSummaryPath)) {
    throw "Missing live-run summary: $LiveSummaryPath"
}
$LiveSummary = Get-Content -Raw -Encoding utf8 $LiveSummaryPath | ConvertFrom-Json
if (-not $LiveSummary.same_prompt_across_runs) {
    throw "Live report runs do not use the same rendered prompt."
}
if ($LiveSummary.aggregate.model_call_success_count -ne $LiveSummary.aggregate.run_count) {
    throw "Not every report run is a successful live model call."
}

if (-not $SkipDemo) {
    Push-Location $RepoRoot
    try {
        & python "D1_D3_demo\run_calibration.py" --check --repeat 3 --runtime-sec 3
        if ($LASTEXITCODE -ne 0) {
            throw "D1/D3 validation failed; PDF compilation was stopped."
        }
    }
    finally {
        Pop-Location
    }
}

if (-not (Test-Path -LiteralPath $SummaryPath)) {
    throw "Missing validation summary: $SummaryPath"
}
$Summary = Get-Content -Raw -Encoding utf8 $SummaryPath | ConvertFrom-Json
if (-not $Summary.overall_pass) {
    throw "Validation summary is not passing; PDF compilation was stopped."
}
if (-not (Test-Path -LiteralPath $ManifestPath)) {
    throw "Missing validation manifest: $ManifestPath"
}
$Manifest = Get-Content -Raw -Encoding utf8 $ManifestPath | ConvertFrom-Json
if (-not $Manifest.overall_pass) {
    throw "Validation manifest is not passing; PDF compilation was stopped."
}
foreach ($Artifact in $Manifest.artifact_index) {
    $ArtifactPath = Join-Path (Join-Path $DemoRoot "results") $Artifact.path
    if (-not (Test-Path -LiteralPath $ArtifactPath)) {
        throw "Manifest artifact is missing: $ArtifactPath"
    }
    $ActualArtifactHash = (Get-FileHash -LiteralPath $ArtifactPath -Algorithm SHA256).Hash
    if ($ActualArtifactHash -ne $Artifact.sha256) {
        throw "Manifest artifact SHA256 mismatch: $ArtifactPath"
    }
}

New-Item -ItemType Directory -Force $BuildDir | Out-Null
Push-Location (Join-Path $DemoRoot "docs")
try {
    & $TectonicExe -X compile --reruns 2 --keep-logs --outdir $BuildDir "$DocumentName.tex"
    if ($LASTEXITCODE -ne 0) {
        throw "Tectonic compilation failed."
    }
}
finally {
    Pop-Location
}

$BuiltPdf = Join-Path $BuildDir "$DocumentName.pdf"
$FinalPdf = Join-Path $RepoRoot "$DocumentName.pdf"
Copy-Item -LiteralPath $BuiltPdf -Destination $FinalPdf -Force
$SourceTex = Join-Path (Join-Path $DemoRoot "docs") "$DocumentName.tex"
$DocumentRecord = [pscustomobject]@{
    path = "$DocumentName.pdf"
    size_bytes = (Get-Item -LiteralPath $FinalPdf).Length
    sha256 = (Get-FileHash -LiteralPath $FinalPdf -Algorithm SHA256).Hash.ToLowerInvariant()
    source_tex = "D1_D3_demo/docs/$DocumentName.tex"
    source_tex_sha256 = (Get-FileHash -LiteralPath $SourceTex -Algorithm SHA256).Hash.ToLowerInvariant()
    calibration_runner = "D1_D3_demo/run_calibration.py"
    calibration_runner_sha256 = (Get-FileHash -LiteralPath (Join-Path $DemoRoot "run_calibration.py") -Algorithm SHA256).Hash.ToLowerInvariant()
    generation_runner = "D1_D3_demo/run_demo.py"
    generation_runner_sha256 = (Get-FileHash -LiteralPath (Join-Path $DemoRoot "run_demo.py") -Algorithm SHA256).Hash.ToLowerInvariant()
    live_aggregator = "D1_D3_demo/aggregate_live_runs.py"
    live_aggregator_sha256 = (Get-FileHash -LiteralPath (Join-Path $DemoRoot "aggregate_live_runs.py") -Algorithm SHA256).Hash.ToLowerInvariant()
    report_config = "D1_D3_demo/report_config.json"
    report_config_sha256 = (Get-FileHash -LiteralPath $ReportConfigPath -Algorithm SHA256).Hash.ToLowerInvariant()
    live_summary = "D1_D3_demo/results/live/live_summary.json"
    live_summary_sha256 = (Get-FileHash -LiteralPath $LiveSummaryPath -Algorithm SHA256).Hash.ToLowerInvariant()
    build_script = "D1_D3_demo/build_pdf.ps1"
    build_script_sha256 = (Get-FileHash -LiteralPath $MyInvocation.MyCommand.Path -Algorithm SHA256).Hash.ToLowerInvariant()
    tectonic_version = $TectonicVersion
    built_at_utc = [DateTime]::UtcNow.ToString("o")
}
$Manifest | Add-Member -NotePropertyName document -NotePropertyValue $DocumentRecord -Force
$Utf8NoBom = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllText(
    $ManifestPath,
    ($Manifest | ConvertTo-Json -Depth 20) + [Environment]::NewLine,
    $Utf8NoBom
)
Write-Host "Built: $FinalPdf"
