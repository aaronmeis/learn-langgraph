# Running Examples A-I Independently

All examples can be run independently. Each Python file has a `if __name__ == "__main__"` block and can be executed directly.

## Prerequisites

Before running any example:

1. **Activate virtual environment:**
   ```cmd
   venv\Scripts\activate.bat
   ```
   or in PowerShell:
   ```powershell
   venv\Scripts\Activate.ps1
   ```

2. **For examples B-I (require Ollama):**
   - Start Ollama in a separate terminal: `ollama serve`
   - Download model: `ollama pull llama3.2:1b`

## Running Each Example

### A: Simple Graph (`simple_graph.py`)
**No LLM required** - Runs immediately!

```cmd
python simple_graph.py
```

**Expected:** Sentiment analysis results for test inputs.

---

### B: LLM Graph (`llm_graph.py`)
**Requires Ollama**

```cmd
python llm_graph.py
```

**Expected:** LLM-powered sentiment analysis with confidence scores and reasoning.

---

### C: Chat Loop (`chat_loop.py`)
**Requires Ollama**

```cmd
# Non-interactive demo mode
python chat_loop.py --demo

# Interactive mode (remove --demo)
python chat_loop.py
```

**Expected:** Multi-turn conversation loop (interactive or demo mode).

---

### D: Persistent Chat (`persistent_chat.py`)
**Requires Ollama**

```cmd
python persistent_chat.py
```

**Expected:** Conversations with memory that persist across runs using thread IDs.

---

### E: Tool Agent (`tool_agent.py`)
**Requires Ollama**

```cmd
python tool_agent.py
```

**Expected:** ReAct agent that reasons, calls tools (time, calculate, weather), and provides answers.

---

### F: Advanced Pipeline (`advanced_pipeline.py`)
**Requires Ollama**

```cmd
python advanced_pipeline.py
```

**Expected:** 7-step document processing pipeline. Output saved to `_outputs/pipeline_output.json`

---

### G: Requirements Transformer (`requirements_transformer.py`)
**Requires Ollama**

```cmd
python requirements_transformer.py
```

**Expected:** CLI interface with human review checkpoints. Output saved to `_outputs/transformed_*.md`

---

### H: General Examples Web App (`app.py`)
**Requires Ollama**

```cmd
python app.py
```

**Then open:** http://localhost:8080 in your browser

**Expected:** Interactive web interface with tabs for examples A-E.

---

### I: Transformer Web App (`transformer_app.py`)
**Requires Ollama**

```cmd
python transformer_app.py
```

**Then open:** http://localhost:5001 in your browser

**Expected:** Visual pipeline with HITL approval buttons and real-time progress.

---

## Quick Reference Table

| Example | File | Command | Requires Ollama | Output |
|---------|------|---------|----------------|--------|
| **A** | `simple_graph.py` | `python simple_graph.py` | ❌ | Console output |
| **B** | `llm_graph.py` | `python llm_graph.py` | ✅ | Console output |
| **C** | `chat_loop.py` | `python chat_loop.py --demo` | ✅ | Console output |
| **D** | `persistent_chat.py` | `python persistent_chat.py` | ✅ | Console output |
| **E** | `tool_agent.py` | `python tool_agent.py` | ✅ | Console output |
| **F** | `advanced_pipeline.py` | `python advanced_pipeline.py` | ✅ | `_outputs/pipeline_output.json` |
| **G** | `requirements_transformer.py` | `python requirements_transformer.py` | ✅ | `_outputs/transformed_*.md` |
| **H** | `app.py` | `python app.py` | ✅ | Web UI at http://localhost:8080 |
| **I** | `transformer_app.py` | `python transformer_app.py` | ✅ | Web UI at http://localhost:5001 |

---

## Notes

- **All examples are independent** - Each can be run without running others
- **Virtual environment must be activated** - You should see `(venv)` in your prompt
- **Web apps (H & I)** - Keep the terminal running while using the web interface
- **Output files** - Generated files are saved in the `_outputs/` directory
- **Ollama must be running** - For examples B-I, ensure `ollama serve` is running in a separate terminal

---

## Troubleshooting

### "Module not found" errors
- Make sure virtual environment is activated (`(venv)` should appear in prompt)
- Run: `pip install -r requirements.txt`

### "Ollama connection refused"
- Start Ollama: `ollama serve` (in separate terminal)
- Verify: `ollama list` should show your models

### Port already in use (for web apps)
- Close other applications using ports 8080 or 5001
- Or change the port in the Python file

---

## Viewing Instructions in Demo Page

To see these instructions with agent videos:

```cmd
python run_demo.py
```

Then open http://localhost:8000/demo.html and select any example from the dropdown. The "Try It Out" section shows detailed instructions for running that specific example.

