# 🚀 LangGraph Demo - Complete Setup Guide

This guide will walk you through setting up and running the LangGraph Demo project on your local machine.

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Step 1: Verify Python Installation](#step-1-verify-python-installation)
3. [Step 2: Install Ollama](#step-2-install-ollama)
4. [Step 3: Download and Prepare the Project](#step-3-download-and-prepare-the-project)
5. [Step 4: Install Python Dependencies](#step-4-install-python-dependencies)
5. [Step 5: Download Ollama Model](#step-5-download-ollama-model)
6. [Step 6: Verify Installation](#step-6-verify-installation)
7. [Step 7: Run Your First Example](#step-7-run-your-first-example)
8. [Troubleshooting](#troubleshooting)

---

## Prerequisites

Before you begin, ensure you have:

- **Python 3.9 or higher** (Python 3.10+ recommended)
- **Internet connection** (for downloading dependencies and Ollama models)
- **At least 4GB RAM** (8GB+ recommended for running LLM examples)
- **5-10GB free disk space** (for Python packages and Ollama models)

---

## Step 1: Verify Python Installation

### Windows

1. Open **Command Prompt** or **PowerShell**
2. Check your Python version:
   ```powershell
   python --version
   ```
   or
   ```powershell
   python3 --version
   ```

3. If Python is not installed:
   - Download from [python.org](https://www.python.org/downloads/)
   - **Important**: Check "Add Python to PATH" during installation
   - Restart your terminal after installation

### macOS

1. Open **Terminal**
2. Check your Python version:
   ```bash
   python3 --version
   ```

3. If Python is not installed:
   ```bash
   # Using Homebrew (recommended)
   brew install python3
   
   # Or download from python.org
   ```

### Linux

1. Open **Terminal**
2. Check your Python version:
   ```bash
   python3 --version
   ```

3. If Python is not installed:
   ```bash
   # Ubuntu/Debian
   sudo apt update
   sudo apt install python3 python3-pip

   # Fedora
   sudo dnf install python3 python3-pip

   # Arch Linux
   sudo pacman -S python python-pip
   ```

**Expected Output**: `Python 3.9.x` or higher

---

## Step 2: Install Ollama

Ollama is required for running LLM-powered examples. It runs locally on your machine.

### Windows

1. **Download Ollama**:
   - Visit [https://ollama.com/download](https://ollama.com/download)
   - Download the Windows installer
   - Run the installer and follow the prompts

2. **Verify Installation**:
   ```powershell
   ollama --version
   ```

3. **Start Ollama** (if not running automatically):
   - Ollama should start automatically as a Windows service
   - If needed, you can start it manually:
     ```powershell
     ollama serve
     ```
   - Keep this terminal window open, or run it in the background

### macOS

1. **Download Ollama**:
   - Visit [https://ollama.com/download](https://ollama.com/download)
   - Download the macOS installer
   - Open the `.dmg` file and drag Ollama to Applications

2. **Verify Installation**:
   ```bash
   ollama --version
   ```

3. **Start Ollama**:
   - Ollama runs automatically as a background service on macOS
   - You can verify it's running:
     ```bash
     curl http://localhost:11434
     ```

### Linux

1. **Install Ollama**:
   ```bash
   curl -fsSL https://ollama.com/install.sh | sh
   ```

2. **Verify Installation**:
   ```bash
   ollama --version
   ```

3. **Start Ollama** (if not running automatically):
   ```bash
   ollama serve
   ```

**Note**: Keep Ollama running in a separate terminal window, or configure it to run as a service.

---

## Step 3: Download and Prepare the Project

1. **Navigate to the project directory**:
   ```bash
   # Windows (PowerShell)
   cd C:\Users\learn\Downloads\LangGraphDemo\LangGraph

   # macOS/Linux
   cd ~/Downloads/LangGraphDemo/LangGraph
   ```

2. **Verify you're in the correct directory**:
   ```bash
   # Windows
   dir

   # macOS/Linux
   ls
   ```

   You should see files like:
   - `requirements.txt`
   - `simple_graph.py`
   - `app.py`
   - `README.md`

---

## Step 4: Install Python Dependencies

1. **Create a virtual environment** (recommended):
   
   **Windows**:
   ```powershell
   python -m venv venv
   venv\Scripts\activate
   ```

   **macOS/Linux**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

   You should see `(venv)` in your terminal prompt.

2. **Upgrade pip** (recommended):
   ```bash
   # Windows
   python -m pip install --upgrade pip

   # macOS/Linux
   python3 -m pip install --upgrade pip
   ```

3. **Install project dependencies**:
   ```bash
   # Windows
   pip install -r requirements.txt

   # macOS/Linux
   pip3 install -r requirements.txt
   ```

   This will install:
   - `langgraph` - Core LangGraph library
   - `pydantic` - Data validation
   - `langchain-core` - LangChain core functionality
   - `openai` - OpenAI-compatible API client (for Ollama)
   - `flask` - Web framework for web examples
   - `requests` - HTTP library

4. **Verify installation**:
   ```bash
   pip list | findstr langgraph
   # or on macOS/Linux:
   pip3 list | grep langgraph
   ```

   You should see `langgraph` in the list.

---

## Step 5: Download Ollama Model

The project uses the `llama3.2:1b` model by default (very fast, good quality), but you can use other models:

1. **Ensure Ollama is running** (check Step 2)

2. **Choose and download a model**:

   **Option A: Fastest (Recommended for quick start)**
   ```bash
   ollama pull tinyllama
   ```
   - Size: ~637MB
   - Speed: Fastest
   - RAM: 2GB+
   - Best for: Quick demos and testing

   **Option B: Very Fast**
   ```bash
   ollama pull llama3.2:1b
   ```
   - Size: ~1.3GB
   - Speed: Very fast
   - RAM: 2GB+
   - Best for: Fast development

   **Option C: Balanced (Default)**
   ```bash
   ollama pull llama3.2
   ```
   - Size: ~2GB
   - Speed: Balanced
   - RAM: 4GB+
   - Best for: Better quality outputs

3. **Verify the model is available**:
   ```bash
   ollama list
   ```

   You should see your chosen model in the list.

4. **Update model in code** (if using a different model):
   
   Edit the `OLLAMA_MODEL` variable in Python files, or use environment variable:
   ```bash
   # Windows PowerShell
   $env:OLLAMA_MODEL="tinyllama"
   
   # macOS/Linux
   export OLLAMA_MODEL="tinyllama"
   ```

**💡 Recommendation**: Start with `tinyllama` for fastest setup and testing. You can always upgrade to `llama3.2` later for better quality.

---

## Step 6: Verify Installation

Let's verify everything is set up correctly:

1. **Test Python dependencies**:
   ```bash
   # Windows
   python -c "import langgraph; print('LangGraph:', langgraph.__version__)"

   # macOS/Linux
   python3 -c "import langgraph; print('LangGraph:', langgraph.__version__)"
   ```

2. **Test Ollama connection**:
   ```bash
   # Windows (PowerShell)
   curl http://localhost:11434/api/tags

   # macOS/Linux
   curl http://localhost:11434/api/tags
   ```

   You should see JSON output with your models listed.

3. **Test a simple example** (no LLM required):
   ```bash
   # Windows
   python simple_graph.py

   # macOS/Linux
   python3 simple_graph.py
   ```

   You should see output showing sentiment analysis results.

---

## Step 7: Run Your First Example

### Example A: Simple Graph (No LLM Required)

This is the simplest example and doesn't require Ollama:

```bash
# Windows
python simple_graph.py

# macOS/Linux
python3 simple_graph.py
```

**Expected Output**: You'll see sentiment analysis results for three test inputs.

### Example B: LLM-Powered Sentiment (Requires Ollama)

This example uses Ollama for intelligent sentiment analysis:

```bash
# Windows
python llm_graph.py

# macOS/Linux
python3 llm_graph.py
```

**Expected Output**: LLM-powered sentiment analysis with reasoning.

### Web Interface: Interactive Examples

Run the Flask web app for an interactive experience:

```bash
# Windows
python app.py

# macOS/Linux
python3 app.py
```

Then open your browser and navigate to:
- **http://localhost:8080**

You'll see a web interface with tabs for different examples.

**Note**: Keep the terminal running while using the web interface.

---

## 🎯 Quick Reference: Running All Examples

| Example | Command | Requires Ollama | Description |
|---------|---------|----------------|-------------|
| **A: Simple** | `python simple_graph.py` | ❌ | Basic sentiment with keywords |
| **B: LLM Sentiment** | `python llm_graph.py` | ✅ | LLM-powered analysis |
| **C: Chat Loop** | `python chat_loop.py --demo` | ✅ | Multi-turn conversation |
| **D: Persistent Chat** | `python persistent_chat.py` | ✅ | Conversations with memory |
| **E: Tool Agent** | `python tool_agent.py` | ✅ | ReAct agent with tools |
| **F: Advanced Pipeline** | `python advanced_pipeline.py` | ✅ | Document processing |
| **G: Transformer (CLI)** | `python requirements_transformer.py` | ✅ | Requirements transformation |
| **H: Web App** | `python app.py` | ✅ | Interactive web UI (port 8080) |
| **I: Transformer Web** | `python transformer_app.py` | ✅ | Transformer web UI (port 5001) |

---

## Troubleshooting

### Issue: "Python is not recognized"

**Solution**:
- Ensure Python is installed and added to PATH
- Try `python3` instead of `python` (macOS/Linux)
- Restart your terminal after installing Python

### Issue: "Ollama is not running" or Connection Errors

**Solution**:
1. Check if Ollama is running:
   ```bash
   ollama list
   ```

2. Start Ollama manually:
   ```bash
   ollama serve
   ```

3. Verify Ollama is accessible:
   ```bash
   curl http://localhost:11434
   ```

4. Check if port 11434 is available (not blocked by firewall)

### Issue: "Module not found" or Import Errors

**Solution**:
1. Ensure you're in the project directory
2. Activate your virtual environment (if using one)
3. Reinstall dependencies:
   ```bash
   pip install -r requirements.txt --upgrade
   ```

### Issue: "Model not found" or Ollama Model Errors

**Solution**:
1. Verify the model is downloaded:
   ```bash
   ollama list
   ```

2. Pull the model again:
   ```bash
   ollama pull llama3.2
   ```

3. Check available disk space (models require several GB)

### Issue: Port Already in Use (8080 or 5001)

**Solution**:
1. Find what's using the port:
   ```bash
   # Windows
   netstat -ano | findstr :8080

   # macOS/Linux
   lsof -i :8080
   ```

2. Either stop the conflicting application or change the port in the Python file:
   - Edit `app.py` line 581: Change `port=8080` to another port
   - Edit `transformer_app.py` to change port 5001

### Issue: Slow LLM Responses

**Solution**:
1. Use a smaller model for faster responses:
   ```bash
   ollama pull llama3.2:1b
   ```
   Then edit the Python files to use `llama3.2:1b` instead of `llama3.2`

2. Ensure you have enough RAM (8GB+ recommended)

3. Close other resource-intensive applications

### Issue: Permission Denied (macOS/Linux)

**Solution**:
```bash
# Make scripts executable (if needed)
chmod +x *.py

# Use python3 explicitly
python3 simple_graph.py
```

### Issue: Virtual Environment Not Activating (Windows)

**Solution**:
```powershell
# If venv\Scripts\activate doesn't work, try:
.\venv\Scripts\Activate.ps1

# If you get an execution policy error:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

---

## 🎓 Next Steps

1. **Explore the Examples**: Start with `simple_graph.py` and work your way through the examples
2. **Read the Code**: Each example is well-commented and demonstrates different LangGraph concepts
3. **Try the Web Interfaces**: Run `app.py` and `transformer_app.py` for interactive experiences
4. **Read the README**: Check `README.md` for detailed explanations of each example
5. **Experiment**: Modify the examples to understand how LangGraph works

---

## 📚 Additional Resources

- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [Ollama Documentation](https://github.com/ollama/ollama)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [Flask Documentation](https://flask.palletsprojects.com/)

---

## ✅ Verification Checklist

Before running examples, verify:

- [ ] Python 3.9+ is installed and accessible
- [ ] Virtual environment is created and activated (optional but recommended)
- [ ] All Python dependencies are installed (`pip install -r requirements.txt`)
- [ ] Ollama is installed and running (`ollama --version`)
- [ ] Ollama model is downloaded (`ollama pull llama3.2:1b` - default, or `ollama pull llama3.2` for better quality)
- [ ] Ollama is accessible (`curl http://localhost:11434`)
- [ ] Simple example runs without errors (`python simple_graph.py`)

---

## 💡 Tips

1. **Use a Virtual Environment**: Keeps dependencies isolated and makes cleanup easier
2. **Keep Ollama Running**: Start it in a separate terminal or configure it as a service
3. **Start Simple**: Begin with `simple_graph.py` (no LLM) before trying LLM examples
4. **Check Logs**: If something fails, check the terminal output for error messages
5. **Read Error Messages**: Most errors include helpful information about what went wrong

---

## 🆘 Getting Help

If you encounter issues not covered here:

1. Check the main `README.md` for example-specific documentation
2. Review the error messages carefully - they often point to the solution
3. Verify each step in this guide was completed successfully
4. Ensure your system meets the prerequisites (Python 3.9+, sufficient RAM)

---

**Happy Coding! 🎉**

