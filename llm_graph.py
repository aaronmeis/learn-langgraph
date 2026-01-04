"""
LangGraph Example A: LLM Integration with Ollama

This example builds on simple_graph.py by replacing the keyword-based
sentiment analysis with an actual LLM call using Ollama (local).

Key differences from simple_graph.py:
- Uses Ollama for local LLM inference (no API key needed!)
- Structured output with Pydantic for LLM responses
- Works great on ARM laptops

Prerequisites:
1. Install Ollama: https://ollama.com/download
2. Pull a model: ollama pull llama3.2
3. Start Ollama (it runs as a service automatically)
"""

import warnings
# Suppress Pydantic V1 deprecation warnings for Python 3.14+
warnings.filterwarnings("ignore", category=UserWarning, module="langchain_core.*")

import json
import sys
from typing import Literal
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, START, END

# OpenAI SDK works with Ollama's OpenAI-compatible API
from openai import OpenAI


def log(message: str):
    """Print with immediate flush for progress visibility."""
    print(message)
    sys.stdout.flush()


# ============================================================
# Configuration
# ============================================================

# Ollama runs locally on port 11434 by default
OLLAMA_BASE_URL = "http://localhost:11434/v1"

# Choose your model (must be pulled first: ollama pull <model>)
# Good options for ARM laptops:
#   - llama3.2 (3B, fast and capable)
#   - llama3.2:1b (1B, very fast)
#   - mistral (7B, if you have 8GB+ RAM)
#   - phi3 (3.8B, good for reasoning)
OLLAMA_MODEL = "llama3.2:1b"


# ============================================================
# Step 1: Define State and LLM Response Models with Pydantic
# ============================================================

class SentimentAnalysis(BaseModel):
    """Structured output for LLM sentiment analysis."""
    sentiment: Literal["positive", "negative", "neutral"] = Field(
        description="The detected sentiment of the text"
    )
    confidence: float = Field(
        description="Confidence score between 0 and 1",
        ge=0.0,
        le=1.0
    )
    reasoning: str = Field(
        description="Brief explanation for the sentiment classification"
    )


class WorkflowState(BaseModel):
    """State that flows through the graph."""
    user_input: str = Field(default="", description="The user's input text")
    processed_input: str = Field(default="", description="Cleaned input")
    word_count: int = Field(default=0, description="Number of words")
    sentiment: Literal["positive", "negative", "neutral"] = Field(
        default="neutral", description="LLM-detected sentiment"
    )
    confidence: float = Field(default=0.0, description="Sentiment confidence")
    reasoning: str = Field(default="", description="LLM's reasoning")
    response: str = Field(default="", description="Final response")


# ============================================================
# Step 2: Create Ollama Client (OpenAI-compatible)
# ============================================================

def get_client() -> OpenAI:
    """
    Get OpenAI-compatible client pointing to Ollama.
    No API key needed for local Ollama!
    """
    return OpenAI(
        base_url=OLLAMA_BASE_URL,
        api_key="ollama"  # Ollama doesn't need a real key, but the SDK requires something
    )


def analyze_sentiment_with_llm(text: str) -> SentimentAnalysis:
    """
    Call Ollama API with structured output using Pydantic.
    Uses JSON mode for reliable parsing.
    """
    log(f"        [Connecting to Ollama at {OLLAMA_BASE_URL}...]")
    client = get_client()
    
    log(f"        [Sending request to {OLLAMA_MODEL}...]")
    log(f"        [Waiting for response (first run loads model into RAM)...]")
    
    response = client.chat.completions.create(
        model=OLLAMA_MODEL,
        temperature=0.0,
        messages=[
            {
                "role": "system",
                "content": """You are a sentiment analysis expert. Analyze the sentiment 
of the given text and classify it as positive, negative, or neutral.

You MUST respond with ONLY a valid JSON object (no other text) containing exactly these fields:
- "sentiment": must be exactly one of "positive", "negative", or "neutral"
- "confidence": a number between 0 and 1 (e.g., 0.85)
- "reasoning": brief explanation for your classification

Example response:
{"sentiment": "positive", "confidence": 0.9, "reasoning": "The text expresses joy and enthusiasm"}"""
            },
            {
                "role": "user",
                "content": f"Analyze the sentiment of this text: {text}"
            }
        ],
        # Note: Ollama supports format: "json" but through OpenAI API we use response_format
    )
    
    content = response.choices[0].message.content.strip()
    
    log(f"        [Response received! Parsing...]")
    
    # Try to extract JSON from response (some models wrap it in markdown)
    if "```json" in content:
        content = content.split("```json")[1].split("```")[0].strip()
    elif "```" in content:
        content = content.split("```")[1].split("```")[0].strip()
    
    # Parse the JSON response into our Pydantic model
    try:
        result_json = json.loads(content)
        return SentimentAnalysis(**result_json)
    except (json.JSONDecodeError, Exception) as e:
        # Fallback if parsing fails
        log(f"[Warning] Could not parse LLM response: {content}")
        return SentimentAnalysis(
            sentiment="neutral",
            confidence=0.5,
            reasoning=f"Parse error, defaulting to neutral. Raw: {content[:100]}"
        )


# ============================================================
# Step 3: Define Node Functions
# ============================================================

def process_input(state: WorkflowState) -> dict:
    """Node 1: Process the raw user input."""
    cleaned = state.user_input.strip()
    words = cleaned.split()
    
    log(f"[Input] Processing: '{cleaned}'")
    log(f"        Word count: {len(words)}")
    
    return {
        "processed_input": cleaned,
        "word_count": len(words)
    }


def analyze_sentiment_llm(state: WorkflowState) -> dict:
    """
    Node 2: Use Ollama LLM for sentiment analysis.
    
    This is the key difference from simple_graph.py - we use an actual
    local LLM with structured output instead of keyword matching.
    """
    log(f"[LLM] Analyzing sentiment with {OLLAMA_MODEL}...")
    
    result = analyze_sentiment_with_llm(state.processed_input)
    
    log(f"[LLM] Result: {result.sentiment} (confidence: {result.confidence:.0%})")
    log(f"[LLM] Reasoning: {result.reasoning}")
    
    return {
        "sentiment": result.sentiment,
        "confidence": result.confidence,
        "reasoning": result.reasoning
    }


def generate_positive_response(state: WorkflowState) -> dict:
    """Node 3a: Generate response for positive sentiment."""
    response = (
        f"I can feel the positivity! ({state.confidence:.0%} confident) "
        f"Your {state.word_count} words radiate good vibes. "
        f"Analysis: {state.reasoning}"
    )
    log("[Response] Generating positive response")
    return {"response": response}


def generate_negative_response(state: WorkflowState) -> dict:
    """Node 3b: Generate response for negative sentiment."""
    response = (
        f"I sense some difficult emotions here. ({state.confidence:.0%} confident) "
        f"It's okay to feel this way. "
        f"Analysis: {state.reasoning}"
    )
    log("[Response] Generating supportive response")
    return {"response": response}


def generate_neutral_response(state: WorkflowState) -> dict:
    """Node 3c: Generate response for neutral sentiment."""
    response = (
        f"Thanks for sharing those {state.word_count} words. ({state.confidence:.0%} confident) "
        f"Analysis: {state.reasoning}"
    )
    log("[Response] Generating neutral response")
    return {"response": response}


# ============================================================
# Step 4: Define Routing Logic
# ============================================================

def route_by_sentiment(state: WorkflowState) -> Literal["positive", "negative", "neutral"]:
    """Route based on LLM-detected sentiment."""
    return state.sentiment


# ============================================================
# Step 5: Build the Graph
# ============================================================

def create_workflow() -> StateGraph:
    """Build and compile the LLM-powered workflow."""
    
    builder = StateGraph(WorkflowState)
    
    # Add nodes
    builder.add_node("process_input", process_input)
    builder.add_node("analyze_sentiment", analyze_sentiment_llm)  # Ollama-powered!
    builder.add_node("positive", generate_positive_response)
    builder.add_node("negative", generate_negative_response)
    builder.add_node("neutral", generate_neutral_response)
    
    # Define flow
    builder.add_edge(START, "process_input")
    builder.add_edge("process_input", "analyze_sentiment")
    
    # Conditional routing
    builder.add_conditional_edges(
        "analyze_sentiment",
        route_by_sentiment,
        {
            "positive": "positive",
            "negative": "negative",
            "neutral": "neutral"
        }
    )
    
    # All responses lead to END
    builder.add_edge("positive", END)
    builder.add_edge("negative", END)
    builder.add_edge("neutral", END)
    
    return builder.compile()


# ============================================================
# Step 6: Run the Workflow
# ============================================================

def check_ollama_running() -> bool:
    """Check if Ollama is running and accessible."""
    try:
        client = get_client()
        client.models.list()
        return True
    except Exception:
        return False


def main():
    """Run the Ollama-powered workflow with test inputs."""
    
    # Check if Ollama is running
    log("Checking Ollama connection...")
    if not check_ollama_running():
        log("=" * 60)
        log("ERROR: Cannot connect to Ollama!")
        log("=" * 60)
        log("\nMake sure Ollama is installed and running:")
        log("\n1. Install Ollama: https://ollama.com/download")
        log(f"\n2. Pull a model:")
        log(f"     ollama pull {OLLAMA_MODEL}")
        log("\n3. Ollama should start automatically as a service.")
        log("   If not, run: ollama serve")
        log(f"\n4. Then run: python llm_graph.py")
        return
    
    log("Ollama is running!")
    log("=" * 60)
    log(f"LangGraph Example A: Local LLM with Ollama ({OLLAMA_MODEL})")
    log("=" * 60)
    
    workflow = create_workflow()
    
    # Test inputs - 3 examples for quick demo
    test_inputs = [
        "I love this amazing day! Everything is wonderful!",
        "This is terrible. I hate when bad things happen.",
        "The weather is cloudy today. I might go for a walk.",
    ]
    
    total_tests = len(test_inputs)
    for i, user_text in enumerate(test_inputs, 1):
        log(f"\n{'-' * 60}")
        log(f"Test {i}/{total_tests}: \"{user_text}\"")
        log("-" * 60)
        
        initial_state = WorkflowState(user_input=user_text)
        result = workflow.invoke(initial_state)
        
        log(f"\n[Final Response]: {result['response']}")
    
    log(f"\n{'=' * 60}")
    log("All tests completed!")
    log("=" * 60)


if __name__ == "__main__":
    main()
