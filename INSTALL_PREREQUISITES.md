# Installing Prerequisites

Before running the LangGraph Demo, you need to install Python and Ollama.

## Step 1: Install Python

### Windows

1. **Download Python**:
   - Go to [https://www.python.org/downloads/](https://www.python.org/downloads/)
   - Click "Download Python 3.x.x" (latest version)
   - The file will be something like `python-3.12.x-amd64.exe`

2. **Install Python**:
   - Run the installer
   - **IMPORTANT**: Check the box "Add Python to PATH" at the bottom
   - Click "Install Now"
   - Wait for installation to complete

3. **Verify Installation**:
   - Open a **new** PowerShell window
   - Run: `python --version`
   - Should show: `Python 3.x.x`

### Troubleshooting Python

**If `python` command doesn't work:**
- Restart PowerShell/terminal after installation
- Check if Python was added to PATH:
  - Search for "Environment Variables" in Windows
  - Edit System Environment Variables
  - Check if Python is in the PATH variable

**Alternative**: Try `py` launcher:
```powershell
py --version
```

---

## Step 2: Install Ollama

### Windows

1. **Download Ollama**:
   - Go to [https://ollama.com/download](https://ollama.com/download)
   - Click "Download for Windows"
   - The file will be `OllamaSetup.exe`

2. **Install Ollama**:
   - Run the installer
   - Follow the installation wizard
   - Ollama will be installed and added to PATH automatically

3. **Verify Installation**:
   - Open a **new** PowerShell window
   - Run: `ollama --version`
   - Should show: `ollama version is 0.x.x`

### Troubleshooting Ollama

**If `ollama` command doesn't work:**
- Restart PowerShell/terminal after installation
- Ollama should be in: `C:\Users\<YourUser>\AppData\Local\Programs\Ollama`
- Check if it's in your PATH

---

## Step 3: Verify Both Are Installed

After installing both, open a **new** PowerShell window and run:

```powershell
python --version
ollama --version
```

Both should show version numbers.

---

## Step 4: Continue Setup

Once Python and Ollama are installed, return to [START_HERE.md](START_HERE.md) and continue from Step 2.

---

## Quick Links

- **Python**: [https://www.python.org/downloads/](https://www.python.org/downloads/)
- **Ollama**: [https://ollama.com/download](https://ollama.com/download)

---

## Need Help?

- Python installation issues: Check [Python.org documentation](https://www.python.org/downloads/windows/)
- Ollama installation issues: Check [Ollama documentation](https://github.com/ollama/ollama)

