@echo off
REM LangGraph Demo Installation Script for CMD
REM Run this AFTER installing Python and Ollama

echo.
echo === LangGraph Demo Installation ===
echo.

REM Check Python
echo Step 1: Checking Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [X] Python not found!
    echo   Please install Python from: https://www.python.org/downloads/
    echo   Make sure to check 'Add Python to PATH' during installation
    pause
    exit /b 1
)
python --version
echo [OK] Python found
echo.

REM Check Ollama
echo Step 2: Checking Ollama...
ollama --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [X] Ollama not found!
    echo   Please install Ollama from: https://ollama.com/download
    pause
    exit /b 1
)
ollama --version
echo [OK] Ollama found
echo.

REM Navigate to project
echo Step 3: Navigating to project...
cd /d "%~dp0"
if %errorlevel% neq 0 (
    echo [X] Failed to navigate to project directory
    pause
    exit /b 1
)
echo [OK] In project directory: %CD%
echo.

REM Create virtual environment
echo Step 4: Creating virtual environment...
if exist venv (
    echo [OK] Virtual environment already exists
) else (
    python -m venv venv
    if %errorlevel% neq 0 (
        echo [X] Failed to create virtual environment
        pause
        exit /b 1
    )
    echo [OK] Virtual environment created
)
echo.

REM Activate virtual environment
echo Step 5: Activating virtual environment...
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
    echo [OK] Virtual environment activated
) else (
    echo [X] Activation script not found
    pause
    exit /b 1
)
echo.

REM Upgrade pip
echo Step 6: Upgrading pip...
python -m pip install --upgrade pip --quiet
if %errorlevel% equ 0 (
    echo [OK] pip upgraded
) else (
    echo [WARNING] pip upgrade had issues, continuing anyway...
)
echo.

REM Install dependencies
echo Step 7: Installing dependencies...
echo   This may take 1-2 minutes...
pip install -r requirements.txt
if %errorlevel% equ 0 (
    echo [OK] All dependencies installed
) else (
    echo [X] Some dependencies failed to install
    echo   Check error messages above
)
echo.

REM Verify installation
echo Step 8: Verifying installation...
pip show langgraph >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] langgraph installed
) else (
    echo [X] langgraph not found
)

pip show flask >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] flask installed
) else (
    echo [X] flask not found
)
echo.

REM Summary
echo === Installation Complete ===
echo.
echo Next steps:
echo 1. Start Ollama (in a NEW terminal):
echo    ollama serve
echo.
echo 2. Download the model (back in this terminal):
echo    ollama pull llama3.2:1b
echo.
echo 3. Run your first example:
echo    python simple_graph.py
echo    OR
echo    python app.py  (then open http://localhost:8080)
echo.
pause

