# LangGraph Demo Setup Verification Script
# Run this script to check your setup

Write-Host "=== LangGraph Demo Setup Verification ===" -ForegroundColor Cyan
Write-Host ""

# Step 1: Check Python
Write-Host "Step 1: Checking Python installation..." -ForegroundColor Yellow
$pythonCmd = Get-Command python -ErrorAction SilentlyContinue
if ($pythonCmd) {
    Write-Host "✓ Python found" -ForegroundColor Green
    python --version
} else {
    Write-Host "✗ Python not found in PATH" -ForegroundColor Red
    Write-Host "  Install from: https://www.python.org/downloads/" -ForegroundColor Yellow
}
Write-Host ""

# Step 2: Check Ollama
Write-Host "Step 2: Checking Ollama installation..." -ForegroundColor Yellow
$ollamaCmd = Get-Command ollama -ErrorAction SilentlyContinue
if ($ollamaCmd) {
    Write-Host "✓ Ollama found" -ForegroundColor Green
    ollama --version
} else {
    Write-Host "✗ Ollama not found in PATH" -ForegroundColor Red
    Write-Host "  Install from: https://ollama.com/download" -ForegroundColor Yellow
}
Write-Host ""

# Step 3: Check project directory
Write-Host "Step 3: Checking project directory..." -ForegroundColor Yellow
Write-Host "Current directory: $(Get-Location)" -ForegroundColor Cyan
if (Test-Path requirements.txt) {
    Write-Host "✓ Project files found" -ForegroundColor Green
} else {
    Write-Host "✗ Not in project directory" -ForegroundColor Red
}
Write-Host ""

# Step 4: Check virtual environment
Write-Host "Step 4: Checking virtual environment..." -ForegroundColor Yellow
if (Test-Path venv) {
    Write-Host "✓ Virtual environment exists" -ForegroundColor Green
} else {
    Write-Host "✗ No virtual environment (create with: python -m venv venv)" -ForegroundColor Yellow
}
Write-Host ""

# Step 5: Check Ollama service
Write-Host "Step 5: Checking Ollama service..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:11434" -TimeoutSec 2 -ErrorAction Stop
    Write-Host "✓ Ollama service is running" -ForegroundColor Green
} catch {
    Write-Host "✗ Ollama service not accessible" -ForegroundColor Red
    Write-Host "  Start with: ollama serve" -ForegroundColor Yellow
}
Write-Host ""

# Step 6: Check models
Write-Host "Step 6: Checking installed models..." -ForegroundColor Yellow
$models = $null
try {
    $models = Invoke-RestMethod -Uri "http://localhost:11434/api/tags" -ErrorAction Stop
}
catch {
    Write-Host "✗ Cannot check models (Ollama not running)" -ForegroundColor Red
}

if ($models -ne $null) {
    if ($models.models.Count -gt 0) {
        Write-Host "✓ Found $($models.models.Count) model(s):" -ForegroundColor Green
        foreach ($model in $models.models) {
            Write-Host "  - $($model.name)" -ForegroundColor Cyan
        }
    } else {
        Write-Host "✗ No models found" -ForegroundColor Yellow
        Write-Host "  Download with: ollama pull llama3.2" -ForegroundColor Cyan
    }
}
Write-Host ""

# Summary
Write-Host "=== Summary ===" -ForegroundColor Cyan
Write-Host "Project directory: $(Get-Location)" -ForegroundColor White
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Install Python 3.9+ if needed" -ForegroundColor White
Write-Host "2. Install Ollama if needed" -ForegroundColor White
Write-Host "3. Create venv: python -m venv venv" -ForegroundColor White
Write-Host "4. Activate: venv\Scripts\Activate.ps1" -ForegroundColor White
Write-Host "5. Install deps: pip install -r requirements.txt" -ForegroundColor White
Write-Host "6. Start Ollama: ollama serve" -ForegroundColor White
Write-Host "7. Pull model: ollama pull llama3.2" -ForegroundColor White
Write-Host "8. Run example: python simple_graph.py" -ForegroundColor White

