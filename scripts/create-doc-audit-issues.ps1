# Create GitHub issues from the Documentation Alignment Audit (2026-09-06)
# Findings already fixed in this session are created then CLOSED (audit trail).
# Remaining findings are created OPEN as a tracked backlog.

$repoOwner = "sean7084"
$repoName = "HengjiAMS1"

$content = Get-Content '.env.local' -Raw
if ($content -match 'GITHUB_CLASSIC_TOKEN=(\S+)') {
    $token = $Matches[1].Trim()
} else {
    Write-Host "ERROR: GITHUB_CLASSIC_TOKEN not found in .env.local" -ForegroundColor Red
    exit 1
}

$headers = @{
    "Authorization" = "Bearer $token"
    "Accept"        = "application/vnd.github.v3+json"
}
$issuesUrl = "https://api.github.com/repos/$repoOwner/$repoName/issues"

$auditRef = "Source: reports/DOCUMENTATION_ALIGNMENT_AUDIT_20260906.md"

# Each issue: title, labels, close (bool), body
$issues = @(
    @{
        title  = "[P0][docs] API_GUIDE.md documented non-existent endpoints, wrong base URL & auth"
        labels = @("documentation", "P0 - Critical")
        close  = $true
        body   = @"
Findings F-01, F-02, F-03, F-04, F-06.

- Base URL was ``/api/`` but real API is ``/api/v1/``.
- Documented JWT/Bearer auth; actual auth is DRF SessionAuthentication (no token endpoint).
- Documented Products/Quotations/Deliveries/Invoices/Reports REST endpoints that do not exist (those are HTML-only views).
- Wrong identifier types (``{uuid}`` vs integer ``<int:pk>``).
- Missing real endpoints (assets by_barcode/by_serial, {id}/assignments, {id}/maintenance).

RESOLVED: ``docs/API_GUIDE.md`` fully rewritten to match ``api/urls.py`` + ``api/views.py`` (9 real viewsets). $auditRef
"@
    },
    @{
        title  = "[P0][security] settings.py hardcoded SECRET_KEY / DEBUG / ALLOWED_HOSTS / database"
        labels = @("security", "P0 - Critical")
        close  = $true
        body   = @"
Findings F-07, F-08.

``hengjiams/settings.py`` hardcoded an insecure ``django-insecure-`` SECRET_KEY, ``DEBUG = True``, ``ALLOWED_HOSTS = ['*']``, and a SQLite database. DEPLOYMENT.md told operators to set SECRET_KEY/DEBUG/ALLOWED_HOSTS/DATABASE_* via env, but none were read - so production could not be configured securely.

RESOLVED: settings.py now reads DJANGO_SECRET_KEY, DJANGO_DEBUG, DJANGO_ALLOWED_HOSTS, and DATABASE_* from the environment with dev-preserving defaults, plus a fail-fast guard (ImproperlyConfigured if DEBUG=False with the insecure key). ``.env.example`` and ``docs/DEPLOYMENT.md`` updated. Verified via ``manage.py check`` in dev and prod modes. $auditRef
"@
    },
    @{
        title  = "[P1][docs] DEPLOYMENT.md: fictional env vars, Docker, run_mailbox_sync, Minimax, template_files"
        labels = @("documentation", "deployment", "P1 - High")
        close  = $true
        body   = @"
Findings F-09, F-10, F-11, F-13.

- Minimax var name/URL wrong (MINIMAX_TOKEN_PLAN_KEY vs lowercase minimax_token_plan_key; api.minimax.io vs api.minimaxi.com/anthropic).
- Referenced a docker/ directory + docker-compose that do not exist.
- Referenced a run_mailbox_sync management command that does not exist (sync is an in-process thread).
- Did not mention that template_files/ is gitignored yet required at runtime (FileNotFoundError).

RESOLVED: DEPLOYMENT.md corrected - env block rewritten to real variables, Docker marked PLANNED/NOT IMPLEMENTED, Step 10 rewritten to describe the in-process sync thread, new Step 4b added for template_files provisioning, extra prod deps flagged. $auditRef
"@
    },
    @{
        title  = "[P1][docs] WORKFLOW_GUIDE.md invoice import logic & tax formula are incorrect"
        labels = @("documentation", "component: invoices", "P1 - High")
        close  = $false
        body   = @"
Findings F-14, F-15.

Invoice import (docs/WORKFLOW_GUIDE.md) does not match ``invoices/services.py::process_sharepoint_batch``:
- Doc says it parses XML/PDF/OFD in a ZIP and regex-extracts amounts; the code reads a single Excel workbook and extracts 3 columns (Kering Group PO Number, Internal Order, SAP Cost Center), with no quotation matching.
- Doc upload route ``/invoices/invoice-info/upload-batch/`` does not exist; real route is ``/invoices/import/``.
- Tax formula inverted: doc uses ``net * rate / (1 + rate)`` (extract from gross); code uses ``line_tax = line_net * rate/100`` then ``gross = net + tax`` (add on top).

Action: rewrite the Invoice Processing Cycle section to match the code. $auditRef
"@
    },
    @{
        title  = "[P2][docs] WORKFLOW_GUIDE.md outdated language codes, Django version, and .env naming"
        labels = @("documentation", "P2 - Medium")
        close  = $false
        body   = @"
Finding F-16.

- Language codes: doc says ``en`` / ``zh-hans``; settings.py defines ``en-us`` / ``zh-cn``.
- Django version: doc says ``django==5.2.3``; requirements.txt pins ``5.2.8``.
- Env file: doc says ``.env.local``; runtime_setup.py loads ``.env``.
- Dispatch stock check references ``Asset.available_count`` and "A-R-Zone" logic; code matches discrete Asset rows by brand+model within INTERNAL_WAREHOUSE_LOCATION_ID (=3).

Action: correct these values in WORKFLOW_GUIDE.md. $auditRef
"@
    },
    @{
        title  = "[P2][docs] SETUP_SUMMARY.md inaccurate counts and self-certification"
        labels = @("documentation", "P2 - Medium")
        close  = $false
        body   = @"
Finding F-17.

- Claims "8 impact classifications"; there are 3 impact labels (breaking change, deprecation, migration-required).
- Claims CODEOWNERS is 116 lines; it was rewritten to 73 lines.
- Self-certifies "API consumers understand available endpoints - Pass", contradicted by the API_GUIDE findings.
- Git snippet typo: ``git add docs/.github/LICENCE CODEOWNERS`` (missing space, misspelled LICENCE).

Action: correct counts, remove/qualify the self-certification, fix the snippet. $auditRef
"@
    },
    @{
        title  = "[P2][bug] DivisionViewSet defined but not registered in the API router"
        labels = @("bug", "component: companies", "P2 - Medium")
        close  = $false
        body   = @"
Finding F-05.

``api/views.py`` defines ``DivisionViewSet`` and the internal ``APIDocumentationView`` lists a ``/api/v1/divisions/`` endpoint, but ``api/urls.py`` never registers it - so the route returns 404 and the class is dead code.

Action: either register ``router.register(r'divisions', DivisionViewSet, basename='division')`` or remove the viewset and its documentation entry. $auditRef
"@
    },
    @{
        title  = "[P1][deployment] requirements.txt missing production dependencies"
        labels = @("deployment", "P1 - High")
        close  = $false
        body   = @"
Finding F-12.

DEPLOYMENT.md assumes a Gunicorn/PostgreSQL/Redis/WhiteNoise production stack, but requirements.txt does not pin:
- gunicorn (WSGI server)
- psycopg2 / psycopg2-binary (PostgreSQL driver - currently commented out)
- whitenoise (static files) and django-redis (caching) - referenced in the performance section

Action: decide the supported production stack and add a requirements section (or a separate requirements-prod.txt), then align DEPLOYMENT.md. $auditRef
"@
    }
)

Write-Host "=== Creating $($issues.Count) issues ===" -ForegroundColor Cyan
$created = 0
$failed = 0

foreach ($issue in $issues) {
    $payload = @{
        title  = $issue.title
        body   = $issue.body
        labels = $issue.labels
    } | ConvertTo-Json -Depth 5

    try {
        $resp = Invoke-RestMethod -Uri $issuesUrl -Method Post -Headers $headers -Body $payload -ContentType "application/json"
        $num = $resp.number
        Write-Host "[+] #$num created: $($issue.title)" -ForegroundColor Green

        if ($issue.close) {
            $closePayload = @{ state = "closed"; state_reason = "completed" } | ConvertTo-Json
            Invoke-RestMethod -Uri "$issuesUrl/$num" -Method Patch -Headers $headers -Body $closePayload -ContentType "application/json" | Out-Null
            Write-Host "    -> closed (resolved this session)" -ForegroundColor DarkGray
        }
        $created++
    } catch {
        Write-Host "[x] FAILED: $($issue.title)" -ForegroundColor Red
        Write-Host "    $($_.Exception.Message)" -ForegroundColor Gray
        Write-Host "    $($_.ErrorDetails.Message)" -ForegroundColor DarkGray
        $failed++
    }
}

Write-Host ""
Write-Host "=== Summary ===" -ForegroundColor Cyan
Write-Host "Created: $created / $($issues.Count)" -ForegroundColor Green
if ($failed -gt 0) { Write-Host "Failed:  $failed" -ForegroundColor Red }
Write-Host "View: https://github.com/$repoOwner/$repoName/issues" -ForegroundColor Yellow
