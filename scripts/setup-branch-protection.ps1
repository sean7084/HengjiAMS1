# Branch Protection Setup for HengjiAMS1
# This script configures branch protection rules for the main branch
# Requires a GitHub token with 'repo' and 'admin:repo' scopes

$repoOwner = "sean7084"
$repoName = "HengjiAMS1"
$branch = "main"

# Read token from .env.local
$content = Get-Content '.env.local' -Raw
if ($content -match 'GITHUB_CLASSIC_TOKEN=(\S+)') {
    $token = $Matches[1].Trim()
} else {
    Write-Host "ERROR: GITHUB_CLASSIC_TOKEN not found in .env.local" -ForegroundColor Red
    Write-Host "Please add your GitHub token to .env.local" -ForegroundColor Yellow
    exit 1
}

$headers = @{
    "Authorization" = "Bearer $token"
    "Accept" = "application/vnd.github.v3+json"
}

$apiUrl = "https://api.github.com/repos/$repoOwner/$repoName/branches/$branch/protection"

Write-Host "=== Setting Up Branch Protection ===" -ForegroundColor Cyan
Write-Host "Repository: $repoOwner/$repoName" -ForegroundColor Yellow
Write-Host "Branch: $branch" -ForegroundColor Yellow
Write-Host ""

# First, verify token works
try {
    $user = Invoke-RestMethod -Uri "https://api.github.com/user" -Headers $headers
    Write-Host "[✓] Token valid. Logged in as: $($user.login)" -ForegroundColor Green
} catch {
    Write-Host "[✗] Token authentication failed: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host ""
    Write-Host "Your token may be expired or lack permissions." -ForegroundColor Yellow
    Write-Host "To fix this:" -ForegroundColor Yellow
    Write-Host "1. Go to: https://github.com/settings/tokens" -ForegroundColor Cyan
    Write-Host "2. Generate a new token with these scopes:" -ForegroundColor Cyan
    Write-Host "   - repo (full control of private repositories)" -ForegroundColor Gray
    Write-Host "   - admin:repo (if available)" -ForegroundColor Gray
    Write-Host "3. Update GITHUB_CLASSIC_TOKEN in .env.local" -ForegroundColor Cyan
    Write-Host "4. Re-run this script" -ForegroundColor Cyan
    exit 1
}

# Configure branch protection
# Note: dismissal_restrictions is only for organization repositories
# For personal repositories, we omit this field
$protectionConfig = @{
    required_status_checks = $null
    enforce_admins = $true
    required_pull_request_reviews = @{
        dismiss_stale_reviews = $true
        require_code_owner_reviews = $true
        required_approving_review_count = 1
    }
    restrictions = $null
} | ConvertTo-Json -Depth 5

Write-Host "Applying branch protection configuration..." -ForegroundColor Cyan
Write-Host "Request body:" -ForegroundColor Gray
Write-Host $protectionConfig -ForegroundColor DarkGray
Write-Host ""

try {
    $response = Invoke-RestMethod `
        -Uri $apiUrl `
        -Method Put `
        -Headers $headers `
        -Body $protectionConfig `
        -ContentType "application/json"
    
    Write-Host ""
    Write-Host "=== SUCCESS ===" -ForegroundColor Green
    Write-Host "Branch protection configured for '$branch' branch!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Applied settings:" -ForegroundColor Cyan
    Write-Host "  ✓ Require pull request before merging" -ForegroundColor Green
    Write-Host "  ✓ Require 1 approving review" -ForegroundColor Green
    Write-Host "  ✓ Dismiss stale reviews automatically" -ForegroundColor Green
    Write-Host "  ✓ Require review from Code Owners" -ForegroundColor Green
    Write-Host "  ✓ Enforce for administrators" -ForegroundColor Green
    Write-Host "  ✓ Block force pushes" -ForegroundColor Green
    Write-Host "  ✓ Block branch deletion" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Yellow
    Write-Host "  1. Test by creating a PR to main branch" -ForegroundColor Gray
    Write-Host "  2. Verify CODEOWNERS triggers automatic review requests" -ForegroundColor Gray
    Write-Host "  3. Confirm PR cannot be merged without approval" -ForegroundColor Gray
    
} catch {
    Write-Host ""
    Write-Host "=== FAILED ===" -ForegroundColor Red
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
    
    # Try to get detailed error using curl
    Write-Host ""
    Write-Host "Getting detailed error from GitHub API..." -ForegroundColor Cyan
    $curlCommand = "curl -s -X PUT -H `"Authorization: Bearer $token`" -H `"Accept: application/vnd.github.v3+json`" -H `"Content-Type: application/json`" -d `'$protectionConfig`' `"$apiUrl`""
    $detailedError = Invoke-Expression $curlCommand 2>&1
    Write-Host "GitHub API Response:" -ForegroundColor Yellow
    Write-Host $detailedError -ForegroundColor Gray
    
    Write-Host ""
    Write-Host "Troubleshooting:" -ForegroundColor Yellow
    Write-Host "  • Ensure token has 'repo' scope" -ForegroundColor Gray
    Write-Host "  • Verify you're a repository admin" -ForegroundColor Gray
    Write-Host "  • Check if branch exists: git branch -a" -ForegroundColor Gray
}
