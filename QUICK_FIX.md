# Quick Fix: ModuleNotFoundError

If you're getting `ModuleNotFoundError: No module named 'pydantic'`, follow these steps:

## Solution

### Step 1: Activate Virtual Environment

**In CMD (Command Prompt):**
```cmd
cd C:\Users\learn\Downloads\LangGraphDemo\LangGraph
venv\Scripts\activate.bat
```

**In PowerShell:**
```powershell
cd C:\Users\learn\Downloads\LangGraphDemo\LangGraph
venv\Scripts\Activate.ps1
```

You should see `(venv)` at the start of your prompt.

### Step 2: Install Dependencies

```cmd
pip install -r requirements.txt
```

Wait for packages to install (1-2 minutes).

### Step 3: Verify Installation

```cmd
python -c "import pydantic; print('✓ pydantic installed')"
```

### Step 4: Run Your Script

```cmd
python llm_graph.py
```

## Alternative: Run Install Script

If you haven't set up the virtual environment yet:

```cmd
install.bat
```

This will:
- Create virtual environment
- Install all dependencies
- Verify installation

## Common Issues

### "venv\Scripts\activate.bat not found"
- Run `install.bat` first to create the virtual environment

### "pip is not recognized"
- Make sure the virtual environment is activated
- You should see `(venv)` in your prompt

### "Permission denied" (PowerShell)
- Run: `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`
- Then try activating again

## Quick Check Commands

```cmd
# Check if venv exists
dir venv

# Check if activated (should show venv path)
echo %VIRTUAL_ENV%

# Check installed packages
pip list | findstr pydantic
```

