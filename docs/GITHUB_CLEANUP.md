# GitHub Actions Cleanup Guide

## Overview

Your CI/CD pipeline creates build artifacts, caches, and workflow runs that accumulate over time. These need to be cleaned up through GitHub's web interface or API.

## Current GitHub Actions Configuration

**Workflow**: `.github/workflows/ci-cd.yml`

**Build Caches**:
- Python pip cache (from `actions/setup-python@v5`)
- Docker build cache (type=gha)

**Artifacts** (retained for 90 days by default):
- `unit-test-results` - pytest cache and coverage reports
- `performance-report` - Locust HTML reports

## What Accumulates

### 1. **Workflow Runs**
- Each push/PR creates a workflow run
- Old runs stay visible indefinitely
- Consume storage quota

### 2. **Build Artifacts**
- Unit test results (`.pytest_cache/`, `htmlcov/`)
- Performance reports (`performance-report.html`)
- Default retention: 90 days
- Count toward storage quota (2 GB free on public repos)

### 3. **Cache Entries**
- Python pip dependencies (~200 MB)
- Docker layer cache (~500 MB - 1 GB)
- Default retention: 7 days if unused
- Max 10 GB per repository

## Manual Cleanup via GitHub Web Interface

### Delete Old Workflow Runs

1. Go to: `https://github.com/superbgithub/-sprint-capacity-api/actions`

2. **Delete Individual Runs**:
   - Click on any workflow run
   - Click the ⋮ (three dots) menu
   - Select "Delete workflow run"

3. **Bulk Delete** (requires GitHub CLI):
   ```bash
   # Install GitHub CLI: https://cli.github.com/
   
   # List all workflow runs
   gh run list --repo superbgithub/-sprint-capacity-api --limit 100
   
   # Delete all completed runs
   gh run list --repo superbgithub/-sprint-capacity-api --limit 100 --json databaseId --jq '.[] | .databaseId' | xargs -I {} gh api repos/superbgithub/-sprint-capacity-api/actions/runs/{} -X DELETE
   ```

### Delete Artifacts

1. Go to: `https://github.com/superbgithub/-sprint-capacity-api/actions/caches`

2. Click on individual artifacts → "Delete artifact"

3. **Or use GitHub CLI**:
   ```bash
   # List artifacts
   gh api repos/superbgithub/-sprint-capacity-api/actions/artifacts
   
   # Delete specific artifact
   gh api repos/superbgithub/-sprint-capacity-api/actions/artifacts/{artifact_id} -X DELETE
   ```

### Clear Caches

1. Go to: `https://github.com/superbgithub/-sprint-capacity-api/actions/caches`

2. Review cache entries (Python pip, Docker layers)

3. Click "Delete" on old/unused caches

4. **Or use GitHub CLI**:
   ```bash
   # List caches
   gh cache list --repo superbgithub/-sprint-capacity-api
   
   # Delete all caches
   gh cache delete --all --repo superbgithub/-sprint-capacity-api
   ```

## Automated Cleanup via GitHub Actions

Add this workflow to automatically clean up old runs and artifacts:

```yaml
# .github/workflows/cleanup.yml
name: Cleanup Old Workflow Runs

on:
  schedule:
    - cron: '0 0 * * 0'  # Run weekly on Sunday at midnight
  workflow_dispatch:  # Allow manual trigger

jobs:
  cleanup:
    runs-on: ubuntu-latest
    
    steps:
      - name: Delete old workflow runs
        uses: Mattraks/delete-workflow-runs@v2
        with:
          token: ${{ github.token }}
          repository: ${{ github.repository }}
          retain_days: 30  # Keep last 30 days
          keep_minimum_runs: 10  # Always keep at least 10 runs
      
      - name: Delete old artifacts
        uses: c-hive/gha-remove-artifacts@v1
        with:
          age: '30 days'  # Delete artifacts older than 30 days
          skip-recent: 5  # Keep last 5 artifacts
```

## PowerShell Script for GitHub CLI Cleanup

Save as `scripts/cleanup-github.ps1`:

```powershell
#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Cleanup GitHub Actions runs, artifacts, and caches
.DESCRIPTION
    Uses GitHub CLI to clean up old workflow runs and artifacts
.PARAMETER KeepDays
    Number of days to keep (default: 30)
#>

param(
    [int]$KeepDays = 30
)

$repo = "superbgithub/-sprint-capacity-api"

Write-Host "=== GitHub Actions Cleanup ===" -ForegroundColor Cyan
Write-Host ""

# Check if GitHub CLI is installed
if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
    Write-Host "❌ GitHub CLI not installed" -ForegroundColor Red
    Write-Host "Install from: https://cli.github.com/" -ForegroundColor Yellow
    exit 1
}

# Check if authenticated
$auth = gh auth status 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Not authenticated with GitHub" -ForegroundColor Red
    Write-Host "Run: gh auth login" -ForegroundColor Yellow
    exit 1
}

Write-Host "✓ GitHub CLI authenticated" -ForegroundColor Green
Write-Host ""

# Calculate cutoff date
$cutoffDate = (Get-Date).AddDays(-$KeepDays).ToString("yyyy-MM-dd")
Write-Host "Deleting items older than: $cutoffDate" -ForegroundColor Yellow
Write-Host ""

# List workflow runs
Write-Host "[1/3] Checking workflow runs..." -ForegroundColor Cyan
$runs = gh run list --repo $repo --limit 1000 --json databaseId,createdAt,status | ConvertFrom-Json

$oldRuns = $runs | Where-Object { 
    $_.status -eq "completed" -and 
    [DateTime]$_.createdAt -lt [DateTime]$cutoffDate 
}

Write-Host "  Total runs: $($runs.Count)" -ForegroundColor Gray
Write-Host "  Completed old runs: $($oldRuns.Count)" -ForegroundColor Yellow

if ($oldRuns.Count -gt 0) {
    $confirm = Read-Host "  Delete $($oldRuns.Count) old workflow runs? (y/N)"
    if ($confirm -eq 'y' -or $confirm -eq 'Y') {
        $oldRuns | ForEach-Object {
            Write-Host "    Deleting run $($_.databaseId)..." -ForegroundColor Gray
            gh api "repos/$repo/actions/runs/$($_.databaseId)" -X DELETE
        }
        Write-Host "  ✓ Workflow runs deleted" -ForegroundColor Green
    }
}

Write-Host ""

# List artifacts
Write-Host "[2/3] Checking artifacts..." -ForegroundColor Cyan
$artifacts = gh api "repos/$repo/actions/artifacts?per_page=100" | ConvertFrom-Json

if ($artifacts.total_count -gt 0) {
    Write-Host "  Found $($artifacts.total_count) artifact(s)" -ForegroundColor Yellow
    
    $confirm = Read-Host "  Delete all artifacts? (y/N)"
    if ($confirm -eq 'y' -or $confirm -eq 'Y') {
        $artifacts.artifacts | ForEach-Object {
            Write-Host "    Deleting artifact: $($_.name)..." -ForegroundColor Gray
            gh api "repos/$repo/actions/artifacts/$($_.id)" -X DELETE
        }
        Write-Host "  ✓ Artifacts deleted" -ForegroundColor Green
    }
} else {
    Write-Host "  ✓ No artifacts found" -ForegroundColor Green
}

Write-Host ""

# List caches
Write-Host "[3/3] Checking caches..." -ForegroundColor Cyan
$caches = gh cache list --repo $repo --json key,sizeInBytes | ConvertFrom-Json

if ($caches.Count -gt 0) {
    $totalSize = ($caches | Measure-Object -Property sizeInBytes -Sum).Sum / 1MB
    Write-Host "  Found $($caches.Count) cache(s) (~$([math]::Round($totalSize, 2)) MB)" -ForegroundColor Yellow
    
    $confirm = Read-Host "  Delete all caches? (y/N)"
    if ($confirm -eq 'y' -or $confirm -eq 'Y') {
        gh cache delete --all --repo $repo
        Write-Host "  ✓ Caches deleted" -ForegroundColor Green
    }
} else {
    Write-Host "  ✓ No caches found" -ForegroundColor Green
}

Write-Host ""
Write-Host "=== Cleanup Complete ===" -ForegroundColor Cyan
```

## Optimize Workflow to Reduce Storage

### 1. Reduce Artifact Retention

```yaml
- name: Upload unit test results
  uses: actions/upload-artifact@v4
  with:
    name: unit-test-results
    path: htmlcov/
    retention-days: 7  # Keep only 7 days instead of default 90
```

### 2. Skip Artifacts for PR Builds

```yaml
- name: Upload performance report
  if: github.ref == 'refs/heads/main'  # Only on main branch
  uses: actions/upload-artifact@v4
  with:
    name: performance-report
    path: performance-report.html
```

### 3. Clean Up Cache in Workflow

```yaml
- name: Clean pip cache
  run: |
    pip cache purge
```

## Check Storage Usage

### Via GitHub Web Interface
1. Go to: `https://github.com/superbgithub/-sprint-capacity-api/settings/billing`
2. View "Actions & Packages" usage

### Via GitHub CLI
```bash
# Check storage usage
gh api repos/superbgithub/-sprint-capacity-api | jq '.size'

# Check Actions storage
gh api /repos/superbgithub/-sprint-capacity-api/actions/cache/usage
```

## Recommended Retention Policies

| Item | Recommended Retention |
|------|----------------------|
| Workflow runs | 30 days |
| Test artifacts | 7 days |
| Performance reports | 14 days |
| Build caches | 7 days (auto-cleanup) |
| Docker caches | Keep latest only |

## Best Practices

1. **Regular Cleanup**
   - Run cleanup script monthly
   - Or add automated workflow (weekly)

2. **Artifact Strategy**
   - Only upload artifacts for main branch
   - Use short retention (7 days for tests, 14 for reports)
   - Don't upload large files (> 100 MB)

3. **Cache Strategy**
   - Use cache keys with branch/date
   - Let GitHub auto-cleanup after 7 days unused
   - Clear cache after major dependency updates

4. **Workflow Strategy**
   - Skip heavy tests on PR commits (only run on merge)
   - Use `if: github.ref == 'refs/heads/main'` for expensive jobs
   - Cancel in-progress runs on new commits

## Links

- **Actions Tab**: https://github.com/superbgithub/-sprint-capacity-api/actions
- **Caches**: https://github.com/superbgithub/-sprint-capacity-api/actions/caches
- **GitHub CLI**: https://cli.github.com/
- **GitHub Docs**: https://docs.github.com/en/actions/managing-workflow-runs
