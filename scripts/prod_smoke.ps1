# prod_smoke.ps1 - Production-style smoke checks
# Usage:
#   .\scripts\prod_smoke.ps1
#   .\scripts\prod_smoke.ps1 -BaseUrl https://api.example.com -AdminToken "..."

param(
    [string]$BaseUrl = "http://127.0.0.1:8787",
    [string]$AdminToken = "",
    [switch]$SkipAdminChecks
)

$ErrorActionPreference = "Stop"

function Invoke-Endpoint {
    param(
        [string]$Method,
        [string]$Path,
        [int[]]$ExpectedStatus,
        [object]$Body = $null,
        [hashtable]$Headers = @{}
    )

    $uri = "$BaseUrl$Path"
    try {
        if ($null -ne $Body) {
            $json = $Body | ConvertTo-Json -Depth 8
            $resp = Invoke-WebRequest -UseBasicParsing -Uri $uri -Method $Method -ContentType "application/json" -Body $json -Headers $Headers
        }
        else {
            $resp = Invoke-WebRequest -UseBasicParsing -Uri $uri -Method $Method -Headers $Headers
        }
        $statusCode = [int]$resp.StatusCode
        $content = $resp.Content
    }
    catch {
        if ($_.Exception.Response) {
            $statusCode = [int]$_.Exception.Response.StatusCode.value__
            $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
            $content = $reader.ReadToEnd()
            $reader.Close()
        }
        else {
            throw "Request failed for $Method ${Path}: $($_.Exception.Message)"
        }
    }

    if ($ExpectedStatus -notcontains $statusCode) {
        throw "Unexpected status for $Method $Path. Expected: $($ExpectedStatus -join ', ') Actual: $statusCode Body: $content"
    }

    return [PSCustomObject]@{ StatusCode = $statusCode; Content = $content }
}

Write-Host "" 
Write-Host "============================================" -ForegroundColor Cyan
Write-Host " BasketScoutDataService - Prod Smoke Check" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "Target: $BaseUrl" -ForegroundColor Yellow
Write-Host ""

$health = Invoke-Endpoint -Method "GET" -Path "/health" -ExpectedStatus @(200)
$healthJson = $health.Content | ConvertFrom-Json
if (-not $healthJson.ok) { throw "/health ok=false" }
Write-Host "[OK] GET /health" -ForegroundColor Green

$providers = Invoke-Endpoint -Method "GET" -Path "/providers/status" -ExpectedStatus @(200)
$providersJson = $providers.Content | ConvertFrom-Json
if (-not $providersJson.providers -or $providersJson.providers.Count -lt 1) {
    throw "/providers/status returned empty provider list"
}
Write-Host "[OK] GET /providers/status" -ForegroundColor Green

$prices = Invoke-Endpoint -Method "GET" -Path "/prices/latest?product=milk" -ExpectedStatus @(200)
$pricesJson = $prices.Content | ConvertFrom-Json
if (-not $pricesJson.items -or $pricesJson.items.Count -lt 1) {
    throw "/prices/latest returned empty items"
}
foreach ($item in $pricesJson.items) {
    if (-not $item.PSObject.Properties.Name.Contains("source")) { throw "Price item missing source" }
    if (-not $item.PSObject.Properties.Name.Contains("confidence")) { throw "Price item missing confidence" }
    if (-not $item.PSObject.Properties.Name.Contains("last_checked_at")) { throw "Price item missing last_checked_at" }
}
Write-Host "[OK] GET /prices/latest?product=milk" -ForegroundColor Green

if (-not $SkipAdminChecks) {
    $adminNoToken = Invoke-Endpoint -Method "GET" -Path "/admin/provider-priority" -ExpectedStatus @(200, 401, 503)

    if ($adminNoToken.StatusCode -eq 200) {
        Write-Host "[WARN] /admin/provider-priority is open (no token required in this environment)." -ForegroundColor Yellow
    }
    else {
        Write-Host "[OK] /admin/provider-priority is protected (status $($adminNoToken.StatusCode))." -ForegroundColor Green
    }

    if ($AdminToken) {
        $headers = @{ "X-Admin-Token" = $AdminToken }
        $adminWithToken = Invoke-Endpoint -Method "GET" -Path "/admin/provider-priority" -ExpectedStatus @(200) -Headers $headers
        $adminJson = $adminWithToken.Content | ConvertFrom-Json
        if (-not $adminJson.priority_order -or $adminJson.priority_order.Count -lt 1) {
            throw "/admin/provider-priority response missing priority_order"
        }
        Write-Host "[OK] /admin/provider-priority with token" -ForegroundColor Green
    }
}

Write-Host ""
Write-Host "[PASS] Production smoke checks passed." -ForegroundColor Green
