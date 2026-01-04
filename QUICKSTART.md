# ⚡ Quick Start Guide

Get up and running in 5 minutes!

## Prerequisites Check

```bash
# Check Python (need 3.9+)
python3 --version

# Check if Ollama is installed
ollama --version
```

## Installation Steps

### 1. Install Ollama (if not installed)

**Windows/macOS**: Download from [ollama.com/download](https://ollama.com/download)

**Linux**:
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

### 2. Navigate to Project Directory

```bash
cd LangGraph
```

### 3. Install Python Dependencies

**Option A: Automated Installer (Recommended)**
```bash
# In CMD: install.bat
# In PowerShell: .\install.ps1
```

**Option B: Manual Install**
```bash
# Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows CMD: venv\Scripts\activate.bat
                         # On Windows PowerShell: venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

### 4. Download Ollama Model

```bash
# Make sure Ollama is running
ollama serve  # Keep this running in a separate terminal

# Download the default model (used by all examples):
ollama pull llama3.2:1b      # Default: Very fast (~1.3GB), good quality

# OR for even faster:
ollama pull tinyllama        # Fastest (~637MB)
# OR for better quality:
ollama pull llama3.2         # Balanced (~2GB, better quality)
```

**💡 Note**: The code defaults to `llama3.2:1b`. Change `OLLAMA_MODEL` in Python files if you use a different model.

### 5. Run Your First Example

```bash
# Simple example (no LLM needed)
python3 simple_graph.py

# Or start the web interface
python3 app.py
# Then open http://localhost:8080
```

## That's It! 🎉

For detailed setup instructions, see [SETUP.md](SETUP.md)

For example descriptions, see [README.md](README.md)

