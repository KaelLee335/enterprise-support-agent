param(
    [int]$Port = 8502
)

$ErrorActionPreference = 'Stop'
$serverUrl = "http://localhost:$Port"
$portProbe = [System.Net.Sockets.TcpClient]::new()
try {
    $connectTask = $portProbe.ConnectAsync('127.0.0.1', $Port)
    $portInUse = $connectTask.Wait(700) -and $portProbe.Connected
}
catch {
    $portInUse = $false
}
finally {
    $portProbe.Dispose()
}

if ($portInUse) {
    try {
        $existingPage = Invoke-WebRequest -Uri $serverUrl -TimeoutSec 3 -UseBasicParsing
        if ($existingPage.StatusCode -eq 200 -and $existingPage.Content -match 'streamlit') {
            Start-Process -FilePath $serverUrl
            "Streamlit is already running at $serverUrl; opened the existing demo."
            return
        }
    }
    catch {
        # Report the occupied port below without exposing response details.
    }
    throw "Port $Port is already in use by another process. Stop it or choose another port with -Port."
}

$previousApiKey = $env:DIFY_API_KEY
$previousBaseUrl = $env:DIFY_BASE_URL
$keyPointer = [IntPtr]::Zero
$secureKey = $null

try {
    if ([string]::IsNullOrWhiteSpace($env:DIFY_API_KEY)) {
        $secureKey = Read-Host 'Paste the Dify app API key (input is hidden)' -AsSecureString
        $keyPointer = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secureKey)
        $env:DIFY_API_KEY = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($keyPointer)
    }
    if ([string]::IsNullOrWhiteSpace($env:DIFY_API_KEY)) {
        throw 'The API key cannot be empty.'
    }

    if ([string]::IsNullOrWhiteSpace($env:DIFY_BASE_URL)) {
        $env:DIFY_BASE_URL = 'http://localhost/v1'
    }

    $projectRoot = Split-Path -Parent $PSScriptRoot
    $python = Join-Path $projectRoot '.venv\Scripts\python.exe'
    if (-not (Test-Path -LiteralPath $python)) {
        throw 'Project virtual environment not found. Run: python -m pip install -r requirements.txt'
    }

    Push-Location $projectRoot
    try {
        & $python -m streamlit run ui/app.py --server.address localhost --server.port $Port
        if ($LASTEXITCODE -ne 0) {
            throw "Streamlit exited with code $LASTEXITCODE."
        }
    }
    finally {
        Pop-Location
    }
}
finally {
    $env:DIFY_API_KEY = $previousApiKey
    $env:DIFY_BASE_URL = $previousBaseUrl
    if ($keyPointer -ne [IntPtr]::Zero) {
        [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($keyPointer)
    }
    if ($secureKey) { $secureKey.Dispose() }
}
