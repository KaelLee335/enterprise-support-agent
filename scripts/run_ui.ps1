param(
    [int]$Port = 8502
)

$ErrorActionPreference = 'Stop'
$previousApiKey = $env:DIFY_API_KEY
$previousBaseUrl = $env:DIFY_BASE_URL
$secureKey = Read-Host 'Paste the Dify app API key (input is hidden)' -AsSecureString
$keyPointer = [IntPtr]::Zero

try {
    $keyPointer = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secureKey)
    $env:DIFY_API_KEY = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($keyPointer)
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
