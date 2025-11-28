# Script to run acceptance tests locally with correct database credentials

Write-Host "🧪 Running Acceptance Tests Locally" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan

# Set database URL for tests
$env:DATABASE_URL = "postgresql+asyncpg://sprint_user:sprint_password@localhost:5432/sprint_capacity_test"

# Initialize database schema
Write-Host "`n📊 Initializing test database..." -ForegroundColor Yellow
python scripts/init_test_db.py

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to initialize database" -ForegroundColor Red
    exit 1
}

# Run acceptance tests
Write-Host "`n🧪 Running acceptance tests..." -ForegroundColor Yellow
pytest tests/acceptance/ -v --tb=short

Write-Host "`nTests complete!" -ForegroundColor Green
