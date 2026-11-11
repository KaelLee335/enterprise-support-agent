$ErrorActionPreference = 'Stop'
$secureKey = $null
$keyPointer = [IntPtr]::Zero
$plainKey = $null

try {
    $secureKey = Read-Host 'Paste the Dify app API key (input is hidden)' -AsSecureString
    $keyPointer = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secureKey)
    $plainKey = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($keyPointer)
    if ([string]::IsNullOrWhiteSpace($plainKey)) {
        throw 'The API key cannot be empty.'
    }

    $baseUrl = $env:DIFY_BASE_URL
    if ([string]::IsNullOrWhiteSpace($baseUrl)) {
        $baseUrl = 'http://localhost/v1'
    }
    $baseUrl = $baseUrl.TrimEnd('/')
    $parametersUrl = if ($baseUrl.EndsWith('/parameters')) { $baseUrl } else { "$baseUrl/parameters" }

    try {
        Invoke-RestMethod -Method Get -Uri $parametersUrl -Headers @{ Authorization = "Bearer $plainKey" } -TimeoutSec 10 | Out-Null
    }
    catch {
        $statusCode = $null
        if ($_.Exception.Response -and $_.Exception.Response.StatusCode) {
            $statusCode = [int]$_.Exception.Response.StatusCode
        }
        if ($statusCode -eq 401 -or $statusCode -eq 403) {
            throw 'Dify rejected the key. Copy an app API key from the API access page of the intended Dify app.'
        }
        throw 'Could not validate the key against Dify. Check DIFY_BASE_URL and confirm the Dify service is running.'
    }

    [Environment]::SetEnvironmentVariable('DIFY_API_KEY', $plainKey, 'User')
    [Environment]::SetEnvironmentVariable('DIFY_BASE_URL', $baseUrl, 'User')
    $env:DIFY_API_KEY = $plainKey
    $env:DIFY_BASE_URL = $baseUrl
    'Dify API key validated and saved in the current Windows user environment. It was not written to project files.'
}
finally {
    $plainKey = $null
    if ($keyPointer -ne [IntPtr]::Zero) {
        [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($keyPointer)
    }
    if ($secureKey) { $secureKey.Dispose() }
}
