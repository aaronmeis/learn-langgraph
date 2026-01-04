# LangGraph Demo Installation Script
# Run this AFTER installing Python and Ollama

Write-Host "=== LangGraph Demo Installation ===" -ForegroundColor Cyan
Write-Host ""

# Check Python
Write-Host "Step 1: Checking Python..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✓ Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Python not found!" -ForegroundColor Red
    Write-Host "  Please install Python from: https://www.python.org/downloads/" -ForegroundColor Yellow
    Write-Host "  Make sure to check 'Add Python to PATH' during installation" -ForegroundColor Yellow
    exit 1
}

# Check Ollama
Write-Host "`nStep 2: Checking Ollama..." -ForegroundColor Yellow
try {
    $ollamaVersion = ollama --version 2>&1
    Write-Host "✓ Ollama found: $ollamaVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Ollama not found!" -ForegroundColor Red
    Write-Host "  Please install Ollama from: https://ollama.com/download" -ForegroundColor Yellow
    exit 1
}

# Navigate to project
Write-Host "`nStep 3: Navigating to project..." -ForegroundColor Yellow
$projectPath = "C:\Users\learn\Downloads\LangGraphDemo\LangGraph"
if (Test-Path $projectPath) {
    Set-Location $projectPath
    Write-Host "✓ In project directory: $(Get-Location)" -ForegroundColor Green
} else {
    Write-Host "✗ Project directory not found: $projectPath" -ForegroundColor Red
    exit 1
}

# Create virtual environment
Write-Host "`nStep 4: Creating virtual environment..." -ForegroundColor Yellow
if (Test-Path venv) {
    Write-Host "✓ Virtual environment already exists" -ForegroundColor Green
} else {
    python -m venv venv
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Virtual environment created" -ForegroundColor Green
    } else {
        Write-Host "✗ Failed to create virtual environment" -ForegroundColor Red
        exit 1
    }
}

# Activate virtual environment
Write-Host "`nStep 5: Activating virtual environment..." -ForegroundColor Yellow
if (Test-Path venv\Scripts\Activate.ps1) {
    & venv\Scripts\Activate.ps1
    Write-Host "✓ Virtual environment activated" -ForegroundColor Green
} else {
    Write-Host "✗ Activation script not found" -ForegroundColor Red
    exit 1
}

# Upgrade pip
Write-Host "`nStep 6: Upgrading pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip --quiet
Write-Host "✓ pip upgraded" -ForegroundColor Green

# Install dependencies
Write-Host "`nStep 7: Installing dependencies..." -ForegroundColor Yellow
Write-Host "  This may take 1-2 minutes..." -ForegroundColor Gray
pip install -r requirements.txt
if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ All dependencies installed" -ForegroundColor Green
} else {
    Write-Host "✗ Some dependencies failed to install" -ForegroundColor Red
    Write-Host "  Check error messages above" -ForegroundColor Yellow
}

# Verify installation
Write-Host "`nStep 8: Verifying installation..." -ForegroundColor Yellow
$langgraph = pip show langgraph 2>&1
if ($langgraph -match "Name: langgraph") {
    Write-Host "✓ langgraph installed" -ForegroundColor Green
} else {
    Write-Host "✗ langgraph not found" -ForegroundColor Red
}

$flask = pip show flask 2>&1
if ($flask -match "Name: flask") {
    Write-Host "✓ flask installed" -ForegroundColor Green
} else {
    Write-Host "✗ flask not found" -ForegroundColor Red
}

# Summary
Write-Host "`n=== Installation Complete ===" -ForegroundColor Cyan
Write-Host "`nNext steps:" -ForegroundColor Yellow
Write-Host "1. Start Ollama (in a NEW terminal):" -ForegroundColor White
Write-Host "   ollama serve" -ForegroundColor Cyan
Write-Host "`n2. Download the model (back in this terminal):" -ForegroundColor White
Write-Host "   ollama pull llama3.2:1b" -ForegroundColor Cyan
Write-Host "`n3. Run your first example:" -ForegroundColor White
Write-Host "   python simple_graph.py" -ForegroundColor Cyan
Write-Host "   OR" -ForegroundColor White
Write-Host "   python app.py  (then open http://localhost:8080)" -ForegroundColor Cyan
Write-Host ""

