$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$appFile = Join-Path $repoRoot "streamlit_app.py"

if (-not (Test-Path -LiteralPath $appFile)) {
    throw "Streamlit app not found: $appFile"
}

function Test-PortInUse {
    param([int]$Port)

    try {
        $listener = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Loopback, $Port)
        $listener.Start()
        $listener.Stop()
        return $false
    } catch {
        return $true
    }
}

$port = 8501
while (Test-PortInUse -Port $port) {
    Write-Host "Port $port is already in use. Trying $($port + 1)..."
    $port += 1
}

Set-Location -LiteralPath $repoRoot

$env:STREAMLIT_SERVER_HEADLESS = "true"
$env:STREAMLIT_SERVER_ADDRESS = "127.0.0.1"
$env:STREAMLIT_SERVER_PORT = "$port"
$env:PYTHONDONTWRITEBYTECODE = "1"

Write-Host "Starting LG refrigerator advisor at http://127.0.0.1:$port"
python -m streamlit run streamlit_app.py --server.address 127.0.0.1 --server.port $port --server.headless true
