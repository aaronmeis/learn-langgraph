"""
LangGraph Example C: Persistent Conversations

This example demonstrates:
- Checkpointing: Save conversation state to resume later
- Thread IDs: Multiple separate conversations
- Memory persistence: State survives between runs

Key concept: LangGraph's checkpointer saves state after each node,
allowing you to resume conversations exactly where you left off.
"""

import warnings
# Suppress Pydantic V1 deprecation warnings for Python 3.14+
warnings.filterwarnings("ignore", category=UserWarning, module="langchain_core.*")

import sys
from typing import Literal
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from openai import OpenAI


# ============================================================
# Configuration
# ============================================================

OLLAMA_BASE_URL = "http://localhost:11434/v1"
OLLAMA_MODEL = "llama3.2:1b"


def log(message: str):
    """Print with immediate flush."""
    print(message)
    sys.stdout.flush()


# ============================================================
# Step 1: Define State
# ============================================================

class Message(BaseModel):
    """A single message in the conversation."""
    role: Literal["user", "assistant"] = Field(description="Who sent the message")
    content: str = Field(description="The message content")


class ChatState(BaseModel):
    """State for persistent conversation."""
    messages: list[Message] = Field(default_factory=list)
    current_input: str = Field(default="")
    turn_count: int = Field(default=0)


# ============================================================
# Step 2: Ollama Client
# ============================================================

def get_client() -> OpenAI:
    return OpenAI(base_url=OLLAMA_BASE_URL, api_key="ollama")


def chat_with_llm(messages: list[Message]) -> str:
    """Send conversation to LLM."""
    client = get_client()
    
    openai_messages = [
        {"role": "system", "content": "You are a helpful assistant. Keep responses concise (1-2 sentences). Remember details the user shares."},
        *[{"role": m.role, "content": m.content} for m in messages]
    ]
    
    response = client.chat.completions.create(
        model=OLLAMA_MODEL,
        temperature=0.7,
        messages=openai_messages,
    )
    
    return response.choices[0].message.content


# ============================================================
# Step 3: Node Functions
# ============================================================

def process_input(state: ChatState) -> dict:
    """Add user message to history."""
    log(f"[Processing] Adding message to history...")
    
    new_message = Message(role="user", content=state.current_input)
    updated_messages = state.messages + [new_message]
    
    return {
        "messages": updated_messages,
        "turn_count": state.turn_count + 1
    }


def generate_response(state: ChatState) -> dict:
    """Generate LLM response."""
    log(f"[LLM] Generating response (turn {state.turn_count})...")
    
    response_text = chat_with_llm(state.messages)
    
    assistant_message = Message(role="assistant", content=response_text)
    updated_messages = state.messages + [assistant_message]
    
    log(f"[Assistant] {response_text}")
    
    return {"messages": updated_messages}


# ============================================================
# Step 4: Build Graph WITH Checkpointer
# ============================================================

def create_persistent_chat():
    """
    Create a chat workflow with memory persistence.
    
    The key difference: we pass a checkpointer to compile()!
    This saves state after each node execution.
    """
    builder = StateGraph(ChatState)
    
    # Add nodes
    builder.add_node("process", process_input)
    builder.add_node("respond", generate_response)
    
    # Simple linear flow (no loop - we control externally)
    builder.add_edge(START, "process")
    builder.add_edge("process", "respond")
    builder.add_edge("respond", END)
    
    # Create checkpointer - this is what enables persistence!
    # MemorySaver stores in RAM (use SqliteSaver for disk persistence)
    checkpointer = MemorySaver()
    
    # Compile WITH the checkpointer
    return builder.compile(checkpointer=checkpointer)


# ============================================================
# Step 5: Demo - Show Persistence Across "Sessions"
# ============================================================

def check_ollama() -> bool:
    try:
        get_client().models.list()
        return True
    except:
        return False


def main():
    """Demonstrate persistent conversations with thread IDs."""
    
    log("=" * 55)
    log("LangGraph Example C: Persistent Conversations")
    log("=" * 55)
    
    log("\nChecking Ollama...")
    if not check_ollama():
        log("ERROR: Ollama not running! Start with: ollama serve")
        return
    log("Ollama connected!")
    
    # Create the persistent workflow
    workflow = create_persistent_chat()
    
    # ========================================
    # Session 1: Start conversation with Alice
    # ========================================
    log("\n" + "=" * 55)
    log("SESSION 1: Starting conversation (thread: alice-123)")
    log("=" * 55)
    
    # The config with thread_id is KEY for persistence
    alice_config = {"configurable": {"thread_id": "alice-123"}}
    
    # First message
    log("\n[User] Hi! My name is Alice and I love pizza.")
    result = workflow.invoke(
        {"current_input": "Hi! My name is Alice and I love pizza."},
        config=alice_config
    )
    
    # Second message in same thread
    log("\n[User] What's a good topping?")
    result = workflow.invoke(
        {"current_input": "What's a good topping?"},
        config=alice_config
    )
    
    # ========================================
    # Session 2: Different user (Bob)
    # ========================================
    log("\n" + "=" * 55)
    log("SESSION 2: Different user (thread: bob-456)")
    log("=" * 55)
    
    bob_config = {"configurable": {"thread_id": "bob-456"}}
    
    log("\n[User] Hello! I'm Bob and I like sushi.")
    result = workflow.invoke(
        {"current_input": "Hello! I'm Bob and I like sushi."},
        config=bob_config
    )
    
    # ========================================
    # Session 3: Return to Alice - SHE IS REMEMBERED!
    # ========================================
    log("\n" + "=" * 55)
    log("SESSION 3: Back to Alice (thread: alice-123)")
    log("=" * 55)
    log(">>> The LLM should remember Alice likes pizza! <<<")
    
    log("\n[User] What's my name and what food do I like?")
    result = workflow.invoke(
        {"current_input": "What's my name and what food do I like?"},
        config=alice_config  # Same thread ID as before!
    )
    
    # ========================================
    # Session 4: Check Bob's memory too
    # ========================================
    log("\n" + "=" * 55)
    log("SESSION 4: Back to Bob (thread: bob-456)")
    log("=" * 55)
    log(">>> The LLM should remember Bob likes sushi! <<<")
    
    log("\n[User] What's my favorite food?")
    result = workflow.invoke(
        {"current_input": "What's my favorite food?"},
        config=bob_config
    )
    
    # ========================================
    # Summary
    # ========================================
    log("\n" + "=" * 55)
    log("PERSISTENCE DEMO COMPLETE!")
    log("=" * 55)
    log("""
Key Takeaways:
1. Each thread_id maintains SEPARATE conversation history
2. Returning to a thread_id resumes where you left off
3. The checkpointer (MemorySaver) stores state automatically
4. For production, use SqliteSaver or PostgresSaver for disk storage
""")


if __name__ == "__main__":
    main()

