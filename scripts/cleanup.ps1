#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Cleanup script for Sprint Capacity API project
.DESCRIPTION
    Removes test data, orphaned Docker volumes, unused images, and cleans up database
#>

Write-Host "=== Sprint Capacity API Cleanup ===" -ForegroundColor Cyan
Write-Host ""

# Function to ask for confirmation
function Confirm-Action {
    param([string]$Message)
    $response = Read-Host "$Message (y/N)"
    return $response -eq 'y' -or $response -eq 'Y'
}

# 1. Clean Database Test Data
Write-Host "[1/5] Checking for test data in database..." -ForegroundColor Yellow
try {
    $testSprints = docker exec postgres psql -U sprint_user -d sprint_capacity -t -c "SELECT COUNT(*) FROM sprints WHERE sprint_number = 'INVALID';" 2>$null
    $testSprintCount = $testSprints.Trim()
    
    if ($testSprintCount -gt 0) {
        Write-Host "  Found $testSprintCount test sprint(s) with 'INVALID' sprint_number" -ForegroundColor Red
        
        if (Confirm-Action "  Remove test data?") {
            docker exec postgres psql -U sprint_user -d sprint_capacity -c "DELETE FROM sprint_assignments WHERE sprint_id IN (SELECT id FROM sprints WHERE sprint_number = 'INVALID');"
            docker exec postgres psql -U sprint_user -d sprint_capacity -c "DELETE FROM sprints WHERE sprint_number = 'INVALID';"
            Write-Host "  ✓ Test data removed" -ForegroundColor Green
        }
    } else {
        Write-Host "  ✓ No test data found" -ForegroundColor Green
    }
} catch {
    Write-Host "  ⚠ Database not running or inaccessible" -ForegroundColor Yellow
}

Write-Host ""

# 2. Clean Orphaned Docker Volumes
Write-Host "[2/5] Checking for orphaned Docker volumes..." -ForegroundColor Yellow
$allVolumes = docker volume ls -q
$usedVolumes = docker ps -a --format "{{.Mounts}}" | ForEach-Object { $_.Split(',') } | Where-Object { $_ }
$namedVolumes = @('workspace_postgres_data', 'workspace_prometheus_data', 'workspace_grafana_data')

$orphanedVolumes = $allVolumes | Where-Object { 
    $volume = $_
    # Keep named volumes and volumes in use
    -not ($namedVolumes -contains $volume) -and -not ($usedVolumes -contains $volume)
}

if ($orphanedVolumes) {
    Write-Host "  Found $($orphanedVolumes.Count) orphaned volume(s)" -ForegroundColor Red
    $orphanedVolumes | ForEach-Object { Write-Host "    - $_" -ForegroundColor Gray }
    
    if (Confirm-Action "  Remove orphaned volumes?") {
        $orphanedVolumes | ForEach-Object { docker volume rm $_ 2>$null }
        Write-Host "  ✓ Orphaned volumes removed" -ForegroundColor Green
    }
} else {
    Write-Host "  ✓ No orphaned volumes found" -ForegroundColor Green
}

Write-Host ""

# 3. Clean Dangling Docker Images
Write-Host "[3/5] Checking for dangling images..." -ForegroundColor Yellow
$danglingImages = docker images -f "dangling=true" -q

if ($danglingImages) {
    Write-Host "  Found $($danglingImages.Count) dangling image(s)" -ForegroundColor Red
    
    if (Confirm-Action "  Remove dangling images?") {
        docker image prune -f | Out-Null
        Write-Host "  ✓ Dangling images removed" -ForegroundColor Green
    }
} else {
    Write-Host "  ✓ No dangling images found" -ForegroundColor Green
}

Write-Host ""

# 4. Clean Stopped Containers
Write-Host "[4/5] Checking for stopped containers..." -ForegroundColor Yellow
$stoppedContainers = docker ps -a -f "status=exited" -q

if ($stoppedContainers) {
    Write-Host "  Found $($stoppedContainers.Count) stopped container(s)" -ForegroundColor Red
    
    if (Confirm-Action "  Remove stopped containers?") {
        docker container prune -f | Out-Null
        Write-Host "  ✓ Stopped containers removed" -ForegroundColor Green
    }
} else {
    Write-Host "  ✓ No stopped containers found" -ForegroundColor Green
}

Write-Host ""

# 5. Clean Python Cache
Write-Host "[5/5] Checking for Python cache files..." -ForegroundColor Yellow
$pycacheDirs = Get-ChildItem -Path . -Recurse -Directory -Filter "__pycache__" -ErrorAction SilentlyContinue
$pycFiles = Get-ChildItem -Path . -Recurse -Filter "*.pyc" -ErrorAction SilentlyContinue

$cacheCount = $pycacheDirs.Count + $pycFiles.Count

if ($cacheCount -gt 0) {
    Write-Host "  Found $cacheCount cache file(s)/folder(s)" -ForegroundColor Red
    
    if (Confirm-Action "  Remove Python cache?") {
        $pycacheDirs | Remove-Item -Recurse -Force
        $pycFiles | Remove-Item -Force
        Write-Host "  ✓ Python cache removed" -ForegroundColor Green
    }
} else {
    Write-Host "  ✓ No Python cache found" -ForegroundColor Green
}

Write-Host ""

# Summary
Write-Host "=== Cleanup Complete ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "Current state:" -ForegroundColor White
Write-Host "  Docker images: $(docker images | Measure-Object -Line | Select-Object -ExpandProperty Lines - 1)" -ForegroundColor Gray
Write-Host "  Docker volumes: $(docker volume ls | Measure-Object -Line | Select-Object -ExpandProperty Lines - 1)" -ForegroundColor Gray
Write-Host "  Docker containers: $(docker ps -a | Measure-Object -Line | Select-Object -ExpandProperty Lines - 1)" -ForegroundColor Gray

Write-Host ""
Write-Host "To see detailed info, run:" -ForegroundColor Yellow
Write-Host "  docker system df" -ForegroundColor Cyan
