$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$appDir = Join-Path $repoRoot "artifacts\lg-advisor"
$appFile = Join-Path $appDir "app.py"

if (-not (Test-Path -LiteralPath $appFile)) {
    throw "Streamlit app not found: $appFile"
}

Set-Location -LiteralPath $appDir

$env:STREAMLIT_SERVER_HEADLESS = "true"
$env:STREAMLIT_SERVER_ADDRESS = "127.0.0.1"
$env:STREAMLIT_SERVER_PORT = "8501"

python -m streamlit run app.py --server.address 127.0.0.1 --server.port 8501 --server.headless true
