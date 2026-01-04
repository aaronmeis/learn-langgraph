# 🚀 START HERE - Run Your First Example

Follow these steps in order to run your first LangGraph example.

## Step 1: Check Prerequisites

Open PowerShell and run:

```powershell
# Check Python
python --version
# Should show Python 3.9.x or higher

# Check Ollama
ollama --version
# Should show a version number
```

**If either is missing:**
- Python: Install from [python.org](https://www.python.org/downloads/)
- Ollama: Install from [ollama.com/download](https://ollama.com/download)

## Step 2: Navigate to Project

```powershell
cd C:\Users\learn\Downloads\LangGraphDemo\LangGraph
```

## Step 3: Create Virtual Environment

**Or use the automated installer:**

**PowerShell:**
```powershell
.\install.ps1
```

**CMD (Command Prompt):**
```cmd
install.bat
```

**Or manually:**
```powershell
python -m venv venv
```

## Step 4: Activate Virtual Environment

**PowerShell:**
```powershell
venv\Scripts\Activate.ps1
```

**CMD (Command Prompt):**
```cmd
venv\Scripts\activate.bat
```

**If you get an execution policy error (PowerShell only):**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```
Then try activating again.

You should see `(venv)` at the start of your prompt.

## Step 5: Install Dependencies

```powershell
pip install -r requirements.txt
```

Wait for packages to install (may take 1-2 minutes).

## Step 6: Start Ollama (in a NEW terminal)

Open a **second PowerShell window** and run:

```powershell
ollama serve
```

**Keep this terminal open** - Ollama needs to keep running.

## Step 7: Download the Model (back in your FIRST terminal)

In your **original terminal** (with venv activated), run:

```powershell
ollama pull llama3.2:1b
```

This downloads ~1.3GB. Wait for it to complete (may take a few minutes).

## Step 8: Run Your First Example! 🎉

### Option A: Simple Example (No LLM - Fastest Test)

```powershell
python simple_graph.py
```

**Expected**: You'll see sentiment analysis results for test inputs.

### Option B: LLM Example (Requires Ollama)

```powershell
python llm_graph.py
```

**Expected**: LLM-powered sentiment analysis with reasoning.

### Option C: Web Interface (Best for Exploring)

```powershell
python app.py
```

Then open your browser to: **http://localhost:8080**

You'll see an interactive web interface with tabs for different examples!

---

## Quick Troubleshooting

### "Python is not recognized"
- Install Python from python.org
- Make sure "Add Python to PATH" is checked during installation
- Restart PowerShell

### "Ollama is not recognized"
- Install Ollama from ollama.com/download
- Restart PowerShell

### "Module not found" errors
- Make sure venv is activated (you should see `(venv)` in prompt)
- Run `pip install -r requirements.txt` again

### "Connection refused" or Ollama errors
- Make sure `ollama serve` is running in a separate terminal
- Check `ollama list` to verify the model is downloaded

---

## What's Next?

After running your first example:

1. **Explore more examples**: See [README.md](README.md) for all available examples
2. **Try the web interface**: Run `python app.py` and explore the tabs
3. **Read the code**: Each example is well-commented and shows different LangGraph concepts
4. **Check detailed docs**: See [SETUP.md](SETUP.md) for comprehensive setup guide

---

## Quick Reference

| Task | Command |
|------|---------|
| Navigate to project | `cd C:\Users\learn\Downloads\LangGraphDemo\LangGraph` |
| Create venv | `python -m venv venv` |
| Activate venv | `venv\Scripts\Activate.ps1` |
| Install deps | `pip install -r requirements.txt` |
| Start Ollama | `ollama serve` (in separate terminal) |
| Pull model | `ollama pull llama3.2:1b` |
| Run simple | `python simple_graph.py` |
| Run web app | `python app.py` → http://localhost:8080 |

---

**Need help?** Check [SETUP.md](SETUP.md) for detailed troubleshooting or [COMMANDS.md](COMMANDS.md) for all commands.

