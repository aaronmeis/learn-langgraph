# LangGraph Examples with Ollama

A complete set of examples demonstrating **LangGraph** with **Pydantic** and **Ollama** (local LLM), including advanced pipelines with Human-in-the-Loop (HITL) and a Flask web interface.

![Overview](./unnamed.png)
## 🎯 Examples Overview

| File | Description | Ollama | HITL | Web UI | Port |
|------|-------------|:------:|:----:|:------:|:----:|
| `simple_graph.py` | Basic graph with keyword sentiment | ❌ | ❌ | ❌ | - |
| `llm_graph.py` | LLM-powered sentiment analysis | ✅ | ❌ | ❌ | - |
| `chat_loop.py` | Multi-turn conversation with loops | ✅ | ❌ | ❌ | - |
| `persistent_chat.py` | Conversations with memory/checkpoints | ✅ | ❌ | ❌ | - |
| `tool_agent.py` | ReAct agent with tool calling | ✅ | ❌ | ❌ | - |
| `advanced_pipeline.py` | Document pipeline with retry/rollback | ✅ | ❌ | ❌ | - |
| `requirements_transformer.py` | Requirements doc transformation | ✅ | ✅ | ❌ | - |
| `app.py` | **Flask Web App** for all examples (A-E) | ✅ | ❌ | ✅ | 8080 |
| `transformer_app.py` | **Flask Web App** for transformation | ✅ | ✅ | ✅ | 5001 |
| `sample_transformer_app.py` | **Flask Web App** with sample file selector | ✅ | ✅ | ✅ | 5002 |
| `run_demo.py` | **Demo Page** with agent videos | ❌ | ❌ | ✅ | 8000 |

## 🚀 Quick Start

> **🎯 NEW USER?** Start here: **[START_HERE.md](START_HERE.md)** - Step-by-step guide to run your first example!

> **📖 More guides:**
> - **[QUICKSTART.md](QUICKSTART.md)** - Get running in 5 minutes
> - **[SETUP.md](SETUP.md)** - Complete step-by-step setup guide with troubleshooting
> - **[COMMANDS.md](COMMANDS.md)** - All commands in one place
> - **[MODELS.md](MODELS.md)** - Guide to choosing the right Ollama model
> - **[RUN_EXAMPLES.md](RUN_EXAMPLES.md)** - How to run each example independently

### Prerequisites

**Quick Install (Recommended):**
```bash
# Run the automated installer (after installing Python and Ollama)
# In CMD: install.bat
# In PowerShell: .\install.ps1
```

**Manual Install:**
```bash
# 1. Install Python dependencies
pip3 install -r requirements.txt

# 2. Install & start Ollama (https://ollama.com/download)
ollama pull llama3.2:1b      # Default model (~1.3GB, very fast, good quality)
# OR for even faster: ollama pull tinyllama (~637MB)
# OR for better quality: ollama pull llama3.2 (~2GB)
ollama serve  # If not running as service (usually runs automatically on macOS)
```

**Note**: On macOS, Ollama typically runs as a background service automatically after installation. You can verify it's running by checking `ollama list` or visiting `http://localhost:11434`.

### Run Examples

```bash
# Basic examples (A-E) - use python3 on macOS
python3 simple_graph.py        # A: No LLM
python3 llm_graph.py           # B: LLM sentiment
python3 chat_loop.py --demo    # C: Chat loop (use --demo for non-interactive)
python3 persistent_chat.py     # D: Checkpointing
python3 tool_agent.py          # E: ReAct agent

# Advanced examples
python3 advanced_pipeline.py   # F: Document pipeline
python3 requirements_transformer.py  # G: Transform requirements (CLI)

# Web Apps (run in separate terminals or background)
python3 app.py                 # General examples web UI - Open http://localhost:8080
python3 transformer_app.py     # Transform requirements (Web) - Open http://localhost:5001
python3 sample_transformer_app.py  # Transform with sample selector - Open http://localhost:5002

# Interactive Demo Page
python3 run_demo.py            # Demo page with agent videos - Open http://localhost:8000/demo.html
```

**Note**: All examples use `python3` command. On some systems, `python` may point to Python 2.x.

---

## 📚 Example Details

### A. Simple Graph (`simple_graph.py`)
**No LLM required** - demonstrates core LangGraph concepts.

```
START → process → analyze → [positive/negative/neutral] → format → END
```

**Concepts**: Pydantic state, nodes, edges, conditional routing

---

### B. LLM Sentiment Analysis (`llm_graph.py`)
Uses Ollama to analyze text sentiment with reasoning.

```
START → analyze_with_llm → route_by_sentiment → [response nodes] → END
```

**Concepts**: OpenAI-compatible API, structured LLM output

---

### C. Multi-turn Chat Loop (`chat_loop.py`)
Interactive conversation that loops until user exits.

```
START → get_input → process → respond → [continue/exit] → get_input...
```

**Concepts**: Graph cycles, conversation history, conditional exit

---

### D. Persistent Chat (`persistent_chat.py`)
Conversations that remember context across sessions.

```python
workflow.invoke(state, config={"configurable": {"thread_id": "user-123"}})
```

**Concepts**: MemorySaver checkpointer, thread IDs

---

### E. Tool-Calling Agent (`tool_agent.py`)
ReAct pattern: Reason → Act → Observe.

```
START → reason → [need_tool/have_answer] → execute_tool → reason...
```

**Tools**: `get_current_time()`, `calculate(expr)`, `get_weather(city)`

---

### F. Advanced Document Pipeline (`advanced_pipeline.py`)
7-step document processing with **retry and rollback** on failure.

```
START → load → parse → extract → prompts → LLM → seed → merge → END
         ↓       ↓                           ↓
      [error_handler] → [retry_router] → retry/rollback
```

**Features**:
- Automatic retry (up to 3 attempts per step)
- Rollback to last successful step
- Detailed progress logging
- JSON output with analysis

**Run**: `python advanced_pipeline.py`
**Output**: `_outputs/pipeline_output.json`
**Diagram**: Open `advanced_pipeline_diagram.html` (also linked in demo page)

---

### G. Requirements Transformer (`requirements_transformer.py`)
Transform generic requirements to IEEE 830 format with **Human-in-the-Loop**.

```
START → load_source → load_template → analyze_mapping 
      → [HUMAN REVIEW] → transform → validate 
      → [HUMAN APPROVAL] → generate → END
```

**Features**:
- Platform detection (Windows/Linux/macOS, ARM/x86)
- Unique run ID (GUID) for each execution
- LLM-assisted mapping analysis
- Two human review checkpoints

**Run**: `python requirements_transformer.py`
**Output**: `_outputs/transformed_ieee830_YYYYMMDD_HHMMSS_xxxxxxxx.md`

**Sample Requirements**: See `requirements/` folder for sample input files (e-commerce, task manager, blog, weather app, fitness tracker)

---

### H. General Examples Web App (`app.py`)
Interactive web interface for examples A-E (Simple, LLM Sentiment, Chat, Persistent Chat, Tool Agent).

```bash
python app.py
# Open http://localhost:8080
```

**Features**:
- Tabbed interface for all 5 basic examples
- Real-time Ollama connection status
- Interactive chat interfaces
- Tool agent with live step-by-step reasoning
- No installation needed - runs in browser

**Note**: Port 8080 is used instead of 5000 to avoid conflicts with macOS AirPlay Receiver.

---

### I. Requirements Transformer Web App (`transformer_app.py`)
Visual web interface for requirements transformation with Human-in-the-Loop.

```bash
python transformer_app.py
# Open http://localhost:5001
```

**Features**:
- Real-time pipeline progress visualization
- Interactive HITL approve/reject buttons
- Document tabs (Source, Template, Output)
- Platform info and Run ID display
- Live log streaming
- Upload or paste requirements documents

### J. Sample Requirements Transformer (`sample_transformer_app.py`)
Web interface with dropdown selector for pre-written sample requirements files.

```bash
python sample_transformer_app.py
# Open http://localhost:5002
```

**Features**:
- Dropdown selector for sample requirements files
- Same transformation pipeline as `transformer_app.py`
- Pre-loaded sample files from `requirements/` folder
- Visual progress tracking
- Human-in-the-Loop checkpoints

**Sample Files Available**:
- E-Commerce Platform
- Task Management Application
- Blog Platform
- Weather Application
- Fitness Tracker

See `requirements/README.md` for details on available samples.

---

## 🔧 Configuration

### Ollama Settings
All LLM examples use (configurable at top of each file):

```python
OLLAMA_BASE_URL = "http://localhost:11434/v1"
OLLAMA_MODEL = "llama3.2:1b"  # Default: fast 1B model. Change to "tinyllama" for even faster, or "llama3.2" for better quality
```

**Quick Model Switch**: To use a faster model, change `OLLAMA_MODEL` in any Python file, or set environment variable:
```bash
# Windows PowerShell
$env:OLLAMA_MODEL="tinyllama"
python llm_graph.py

# macOS/Linux
export OLLAMA_MODEL="tinyllama"
python3 llm_graph.py
```

### Recommended Models (Fastest to Best Quality)

**For fastest setup and testing:**
| Model | Size | Speed | RAM | Best For |
|-------|------|-------|-----|----------|
| `tinyllama` | ~637MB | ⚡⚡⚡ Fastest | 2GB+ | Quick demos, testing |
| `llama3.2:1b` | ~1.3GB | ⚡⚡ Very Fast | 2GB+ | Fast development |
| `gemma:2b` | ~1.4GB | ⚡⚡ Very Fast | 2GB+ | Good quality/speed balance |

**For balanced performance:**
| Model | Size | Speed | RAM | Best For |
|-------|------|-------|-----|----------|
| `llama3.2` | ~2.0GB | ⚡⚡ Balanced | 4GB+ | Better quality (code uses `llama3.2:1b` by default) |
| `phi3:mini` | ~2.3GB | ⚡⚡ Balanced | 4GB+ | Better reasoning tasks |

**For best quality (slower):**
| Model | Size | Speed | RAM | Best For |
|-------|------|-------|-----|----------|
| `llama3.1:8b` | ~4.7GB | ⚡ Slower | 8GB+ | Production quality |
| `mistral` | ~4.1GB | ⚡ Slower | 8GB+ | High quality outputs |

**💡 Recommendation**: Start with `tinyllama` or `llama3.2:1b` for fastest setup, then upgrade to `llama3.2` if you need better quality.

---

## 📁 Project Structure

```
langgraph-learn/
├── simple_graph.py           # A: Basic concepts
├── llm_graph.py              # B: LLM sentiment
├── chat_loop.py              # C: Multi-turn chat
├── persistent_chat.py        # D: Checkpointing
├── tool_agent.py             # E: ReAct agent
├── advanced_pipeline.py      # F: Document pipeline
├── requirements_transformer.py # G: Transform (CLI)
├── app.py                    # H: General examples web UI (port 8080)
├── transformer_app.py        # I: Transform requirements (Web, port 5001)
├── sample_transformer_app.py # J: Transform with sample selector (port 5002)
├── advanced_pipeline_diagram.html # Pipeline visualization
├── requirements.txt          # Dependencies
├── demo.html                 # Interactive demo page with agent videos
├── run_demo.py               # Script to serve demo.html locally
├── requirements/            # Sample requirements documents
│   ├── README.md           # Guide to sample files
│   ├── sample_1_ecommerce.md
│   ├── sample_2_task_manager.md
│   ├── sample_3_blog_platform.md
│   ├── sample_4_weather_app.md
│   └── sample_5_fitness_tracker.md
├── _outputs/                # Generated output files (logs, JSON, MD)
│   └── README.md           # Info about generated files
└── README.md                 # This file
```

---

## 🧠 Key Concepts

### 1. Pydantic State
```python
class WorkflowState(BaseModel):
    messages: list[Message] = Field(default_factory=list)
    current_input: str = ""
```

### 2. Node Functions
```python
def process_input(state: WorkflowState) -> dict:
    return {"processed_input": state.user_input.strip()}
```

### 3. Conditional Routing
```python
builder.add_conditional_edges(
    "analyze",
    route_function,
    {"option_a": "node_a", "option_b": "node_b"}
)
```

### 4. Cycles (Loops)
```python
builder.add_edge("respond", "get_input")  # Creates loop
```

### 5. Checkpointing
```python
from langgraph.checkpoint.memory import MemorySaver
checkpointer = MemorySaver()
workflow = builder.compile(checkpointer=checkpointer)
```

### 6. Human-in-the-Loop
```python
# Route based on human approval
builder.add_conditional_edges(
    "human_review",
    lambda s: "continue" if s.human_approved else "revise",
    {"continue": "next_step", "revise": "previous_step"}
)
```

### 7. Retry/Rollback
```python
# Error handler decides: retry, rollback, or fail
builder.add_conditional_edges(
    "error_handler",
    route_after_error,
    {"step_name": "step_name", "end": END}  # Can route to any step
)
```

---

## 🔗 Resources

- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [Ollama](https://ollama.com/)
- [Pydantic v2](https://docs.pydantic.dev/)
- [Flask](https://flask.palletsprojects.com/)

---

## 🖥️ Platform Support

| Platform | Architecture | Status |
|----------|--------------|--------|
| Windows | x86_64 | ✅ Tested |
| Windows | ARM64 | ✅ Tested |
| Linux | x86_64 | ✅ Supported |
| Linux | ARM64 | ✅ Supported |
| macOS | Intel | ✅ Supported |
| macOS | Apple Silicon | ✅ Supported |

Platform is auto-detected and displayed in the web UI and CLI output.

---

## 🔧 Troubleshooting

### Port Conflicts

**macOS Port 5000 Issue**: macOS uses port 5000 for AirPlay Receiver by default. The `app.py` web interface uses port **8080** instead to avoid conflicts.

If you need to change ports:
- Edit `app.py` line 581: `app.run(debug=True, host='127.0.0.1', port=8080)`
- Edit `transformer_app.py` to change port 5001 if needed
- Edit `sample_transformer_app.py` to change port 5002 if needed
- Edit `run_demo.py` to change port 8000 if needed

### Ollama Connection Issues

If examples fail with "Ollama is not running":
1. Check Ollama is installed: `ollama --version`
2. Start Ollama service: `ollama serve` (or ensure it's running as a service)
3. Verify model is available: `ollama list`
4. Pull model if missing: `ollama pull llama3.2:1b` (or `ollama pull llama3.2` for better quality)

### Python Version

This project requires Python 3.9+. Check your version:
```bash
python3 --version
```

### Dependencies

If you encounter import errors:
```bash
pip3 install -r requirements.txt
```

For ARM Macs (Apple Silicon), all dependencies should install without issues.

---

## 📄 Output Files

When running examples, the following files may be generated:

- **`_outputs/pipeline_output.json`** - Output from `advanced_pipeline.py` with document analysis
- **`_outputs/pipeline_run.log`** - Execution log from pipeline runs
- **`_outputs/app.log`** - Logs from running `app.py`
- **`_outputs/transformer_app.log`** - Logs from running `transformer_app.py`
- **`_outputs/transformed_ieee830_YYYYMMDD_HHMMSS_xxxxxxxx.md`** - Generated requirements documents from transformer
- **`_outputs/output_*.md`** - Various output files from example runs
- **`advanced_pipeline_diagram.html`** - Visual diagram of the pipeline (open in browser, also linked in demo page)

**Note**: All generated output files are stored in the `_outputs/` directory. These files are automatically created when running examples and can be safely deleted. See `_outputs/README.md` for more details.

## ✅ Testing Status

All examples have been tested and verified working on:
- ✅ macOS (Apple Silicon) - All examples passing
- ✅ Python 3.9.6
- ✅ Ollama with llama3.2:1b model (default)
- ✅ All web interfaces accessible
- ✅ All syntax errors fixed in `app.py`

## 🎬 Interactive Demo Page

View all examples with AI agent explanation videos:

```bash
python run_demo.py
```

Then open http://localhost:8000/demo.html in your browser. The demo page includes:
- Interactive example selector
- AI agent video explanations for each example
- Code overviews with detailed snippets
- "Try It Out" instructions for running each example independently

## 📝 Recent Updates

- **Sample Requirements Transformer**: Added `sample_transformer_app.py` with dropdown selector for sample files (port 5002)
- **Sample Requirements Folder**: Created `requirements/` folder with 5 sample requirements documents
- **Interactive Demo**: Added `demo.html` with agent videos and detailed instructions
- **Code Overviews**: Enhanced code examples in demo page for all A-I examples
- **Pipeline Diagram Link**: Added link to `advanced_pipeline_diagram.html` in demo page for Advanced Pipeline example
- **Independent Execution**: All examples can run independently (see [RUN_EXAMPLES.md](RUN_EXAMPLES.md))
- **Model Default**: Updated to `llama3.2:1b` as default for faster performance
- **Compressed Avatars**: All videos now use compressed versions from `avatars/compressed_avatars/` for faster loading
- **Port Fix**: `app.py` uses port 8080 instead of 5000 to avoid macOS AirPlay Receiver conflicts
- **Syntax Fixes**: Fixed indentation errors in `chat_loop.py` and `advanced_pipeline.py`
- **Dark Theme**: Updated `sample_transformer_app.py` with dark theme for better contrast
- **Verified**: All examples tested and working

