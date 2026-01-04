# Setup Commands Walkthrough

Run these commands in order to set up and verify your LangGraph Demo installation.

## Prerequisites Check

### 1. Check Python Installation
```powershell
python --version
```
**Expected**: `Python 3.9.x` or higher  
**If not found**: Install from [python.org](https://www.python.org/downloads/)

### 2. Check Ollama Installation
```powershell
ollama --version
```
**Expected**: Version number (e.g., `ollama version is 0.x.x`)  
**If not found**: Install from [ollama.com/download](https://ollama.com/download)

### 3. Navigate to Project Directory
```powershell
cd C:\Users\learn\Downloads\LangGraphDemo\LangGraph
# Or wherever your project is located
```

### 4. Verify Project Files
```powershell
Get-ChildItem *.py, *.txt
```
**Expected**: Should see `requirements.txt`, `simple_graph.py`, etc.

---

## Setup Steps

### Step 1: Create Virtual Environment
```powershell
python -m venv venv
```
Creates a new virtual environment in the `venv` folder.

### Step 2: Activate Virtual Environment
```powershell
venv\Scripts\Activate.ps1
```
**Note**: If you get an execution policy error, run:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```
Then try activating again.

You should see `(venv)` in your prompt.

### Step 3: Upgrade pip
```powershell
python -m pip install --upgrade pip
```

### Step 4: Install Dependencies
```powershell
pip install -r requirements.txt
```
This installs:
- langgraph
- pydantic
- langchain-core
- openai
- flask
- requests

**Expected output**: Shows packages being installed.

### Step 5: Verify Installation
```powershell
pip list | Select-String langgraph
```
**Expected**: Should show `langgraph` in the list.

---

## Ollama Setup

### Step 6: Start Ollama Service
Open a **new terminal window** and run:
```powershell
ollama serve
```
Keep this terminal open. Ollama will run in the background.

### Step 7: Download Model
In your **original terminal** (with venv activated), download the default model:

**Default (Used by all examples):**
```powershell
ollama pull llama3.2:1b
```
Downloads ~1.3GB - very fast, good quality. This is what the code uses by default.

**Alternative options:**
```powershell
ollama pull tinyllama       # ~637MB, fastest
# OR
ollama pull llama3.2         # ~2GB, better quality
```

### Step 8: Verify Model
```powershell
ollama list
```
**Expected**: Should show your chosen model (e.g., `tinyllama` or `llama3.2`) in the list.

**Note**: The code defaults to `llama3.2:1b`. If you use a different model, update the `OLLAMA_MODEL` variable in the Python files, or set:
```powershell
$env:OLLAMA_MODEL="tinyllama"  # or "llama3.2" for better quality
```

---

## Run Examples

### Test 1: Simple Example (No LLM Required)
```powershell
python simple_graph.py
```
**Expected**: Shows sentiment analysis results for test inputs.

### Test 2: LLM Example (Requires Ollama)
```powershell
python llm_graph.py
```
**Expected**: Shows LLM-powered sentiment analysis.

### Test 3: Web Interface
```powershell
python app.py
```
Then open your browser to: **http://localhost:8080**

---

## Troubleshooting Commands

### Check if Python is in PATH
```powershell
Get-Command python -ErrorAction SilentlyContinue
```

### Check if Ollama is running
```powershell
Invoke-WebRequest -Uri "http://localhost:11434" -TimeoutSec 2
```

### Check installed models
```powershell
Invoke-RestMethod -Uri "http://localhost:11434/api/tags"
```

### Check installed Python packages
```powershell
pip list
```

### Reinstall dependencies
```powershell
pip install -r requirements.txt --upgrade
```

---

## Quick Reference

| Task | Command |
|------|---------|
| Create venv | `python -m venv venv` |
| Activate venv | `venv\Scripts\Activate.ps1` |
| Install deps | `pip install -r requirements.txt` |
| Start Ollama | `ollama serve` |
| Pull model | `ollama pull llama3.2:1b` (default) or `ollama pull llama3.2` (better quality) |
| Run simple | `python simple_graph.py` |
| Run web app | `python app.py` |

---

## Next Steps

After setup is complete:
1. Read [SETUP.md](SETUP.md) for detailed instructions
2. Read [README.md](README.md) for example descriptions
3. Try running different examples from the examples table

