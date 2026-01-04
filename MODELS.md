# Ollama Model Guide

This guide helps you choose the right Ollama model for your needs.

## Quick Comparison

| Model | Size | Speed | RAM | Quality | Best For |
|-------|------|-------|-----|---------|----------|
| `tinyllama` | 637MB | ⚡⚡⚡ Fastest | 2GB+ | Good | **Quick demos, testing** |
| `llama3.2:1b` | 1.3GB | ⚡⚡ Very Fast | 2GB+ | Good | Fast development |
| `gemma:2b` | 1.4GB | ⚡⚡ Very Fast | 2GB+ | Good | Balanced speed/quality |
| `llama3.2` | 2.0GB | ⚡⚡ Balanced | 4GB+ | Better | Better quality (code uses `llama3.2:1b` by default) |
| `phi3:mini` | 2.3GB | ⚡⚡ Balanced | 4GB+ | Better | Reasoning tasks |
| `llama3.1:8b` | 4.7GB | ⚡ Slower | 8GB+ | Best | Production quality |
| `mistral` | 4.1GB | ⚡ Slower | 8GB+ | Best | High quality outputs |

## Recommended Models by Use Case

### 🚀 Fastest Setup (Recommended for First-Time Users)
```bash
ollama pull tinyllama
```
- **Why**: Smallest download (~637MB), fastest responses
- **Perfect for**: Quick testing, demos, learning LangGraph concepts
- **Trade-off**: Slightly lower quality than larger models, but still very capable

### ⚡ Fast Development
```bash
ollama pull llama3.2:1b
```
- **Why**: Very fast, good quality, small footprint
- **Perfect for**: Rapid iteration, development, testing
- **Trade-off**: Good balance of speed and quality

### ⚖️ Balanced (Better Quality)
```bash
ollama pull llama3.2
```
- **Why**: Better quality than `llama3.2:1b`, still fast
- **Perfect for**: When you need better quality than the default `llama3.2:1b`
- **Trade-off**: Larger download (~2GB vs ~1.3GB), needs more RAM (4GB+ vs 2GB+)
- **Note**: Code defaults to `llama3.2:1b` for faster performance

### 🎯 Best Quality
```bash
ollama pull llama3.1:8b
# OR
ollama pull mistral
```
- **Why**: Highest quality outputs
- **Perfect for**: Production, complex reasoning, important tasks
- **Trade-off**: Slower, requires more RAM (8GB+)

## How to Switch Models

### Method 1: Environment Variable (Recommended)
```bash
# Windows PowerShell
$env:OLLAMA_MODEL="tinyllama"
python llm_graph.py

# macOS/Linux
export OLLAMA_MODEL="tinyllama"
python3 llm_graph.py
```

### Method 2: Edit Python Files
Change `OLLAMA_MODEL` in any Python file:
```python
OLLAMA_MODEL = "tinyllama"  # Change from "llama3.2"
```

Files to update:
- `llm_graph.py`
- `chat_loop.py`
- `persistent_chat.py`
- `tool_agent.py`
- `advanced_pipeline.py`
- `requirements_transformer.py`
- `app.py`
- `transformer_app.py`

## Model Details

### tinyllama
- **Parameters**: 1.1B
- **Download**: `ollama pull tinyllama`
- **Size**: ~637MB
- **Speed**: Fastest
- **Quality**: Good for simple tasks, decent for complex ones
- **Best for**: Quick demos, testing, learning

### llama3.2:1b
- **Parameters**: 1B
- **Download**: `ollama pull llama3.2:1b`
- **Size**: ~1.3GB
- **Speed**: Very fast
- **Quality**: Good
- **Best for**: Fast development, quick iterations

### llama3.2 (Default)
- **Parameters**: 3B
- **Download**: `ollama pull llama3.2`
- **Size**: ~2GB
- **Speed**: Balanced
- **Quality**: Better
- **Best for**: Most use cases, good default choice

### phi3:mini
- **Parameters**: 3.8B
- **Download**: `ollama pull phi3:mini`
- **Size**: ~2.3GB
- **Speed**: Balanced
- **Quality**: Better (especially for reasoning)
- **Best for**: Tasks requiring better reasoning

## Performance Tips

1. **Start Small**: Begin with `tinyllama` to get started quickly
2. **Upgrade as Needed**: Switch to larger models if quality isn't sufficient
3. **Multiple Models**: You can have multiple models installed and switch between them
4. **Check Available Models**: `ollama list` shows all installed models
5. **Remove Unused Models**: `ollama rm <model>` to free up disk space

## Troubleshooting

### Model Not Found
```bash
# List available models
ollama list

# Pull the model you need
ollama pull tinyllama
```

### Out of Memory
- Use a smaller model (`tinyllama` or `llama3.2:1b`)
- Close other applications
- Ensure you have enough RAM (2GB+ for tinyllama, 4GB+ for llama3.2)

### Slow Responses
- Use a smaller model
- Ensure Ollama is running: `ollama serve`
- Check system resources (CPU/RAM usage)

## Example: Quick Start with tinyllama

```bash
# 1. Pull the fastest model
ollama pull tinyllama

# 2. Set environment variable
export OLLAMA_MODEL="tinyllama"  # macOS/Linux
# OR
$env:OLLAMA_MODEL="tinyllama"    # Windows PowerShell

# 3. Run examples
python3 llm_graph.py
python3 app.py
```

## Summary

**For fastest setup**: Use `tinyllama` (~637MB, fastest)  
**For balanced use**: Use `llama3.2` (~2GB, good quality)  
**For best quality**: Use `llama3.1:8b` (~4.7GB, best quality)

Start with `tinyllama` and upgrade if needed!

