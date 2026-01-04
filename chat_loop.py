"""
LangGraph Example B: Multi-turn Chat Loop

This example demonstrates:
- Cycles in the graph (looping back for more input)
- Maintaining conversation history in state
- Conditional routing (continue vs end)
- Interactive conversation with Ollama

Graph Structure:
    START
      │
      ▼
    get_input ◄─────────────┐
      │                     │
      ▼                     │
    process_message         │
      │                     │
      ▼                     │
    generate_response       │
"""

import warnings
# Suppress Pydantic V1 deprecation warnings for Python 3.14+
warnings.filterwarnings("ignore", category=UserWarning, module="langchain_core.*")

import sys
from typing import Literal
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, START, END

from openai import OpenAI


# ============================================================
# Configuration
# ============================================================

OLLAMA_BASE_URL = "http://localhost:11434/v1"
OLLAMA_MODEL = "llama3.2:1b"


def log(message: str):
    """Print with immediate flush for progress visibility."""
    print(message)
    sys.stdout.flush()


# ============================================================
# Step 1: Define State with Conversation History
# ============================================================

class Message(BaseModel):
    """A single message in the conversation."""
    role: Literal["user", "assistant"] = Field(description="Who sent the message")
    content: str = Field(description="The message content")


class ChatState(BaseModel):
    """
    State for multi-turn conversation.
    
    Key difference from previous examples: we maintain a LIST of messages
    to track the full conversation history.
    """
    messages: list[Message] = Field(default_factory=list, description="Conversation history")
    current_input: str = Field(default="", description="Current user input")
    should_continue: bool = Field(default=True, description="Whether to continue the loop")
    turn_count: int = Field(default=0, description="Number of conversation turns")


# ============================================================
# Step 2: Create Ollama Client
# ============================================================

def get_client() -> OpenAI:
    """Get OpenAI-compatible client for Ollama."""
    return OpenAI(
        base_url=OLLAMA_BASE_URL,
        api_key="ollama"
    )


def chat_with_llm(messages: list[Message]) -> str:
    """
    Send conversation history to LLM and get response.
    The LLM sees the full conversation context!
    """
    client = get_client()
    
    # Convert our Message objects to OpenAI format
    openai_messages = [
        {"role": "system", "content": "You are a helpful, friendly assistant. Keep responses concise (1-2 sentences)."},
        *[{"role": m.role, "content": m.content} for m in messages]
    ]
    
    response = client.chat.completions.create(
        model=OLLAMA_MODEL,
        temperature=0.7,
        messages=openai_messages,
    )
    
    return response.choices[0].message.content


# ============================================================
# Step 3: Define Node Functions
# ============================================================

def get_user_input(state: ChatState) -> dict:
    """
    Node 1: Get input from user.
    
    In a real app, this might come from an API request.
    Here we use input() for interactive demo.
    """
    log(f"\n[Turn {state.turn_count + 1}]")
    
    if state.turn_count == 0:
        log("Chat started! Type 'bye' to exit.\n")
    
    try:
        user_input = input("You: ")
    except EOFError:
        user_input = "bye"
    
    return {
        "current_input": user_input,
        "turn_count": state.turn_count + 1
    }


def process_message(state: ChatState) -> dict:
    """
    Node 2: Add user message to history.
    """
    # Check for exit commands
    exit_words = {"bye", "exit", "quit", "goodbye"}
    if state.current_input.lower().strip() in exit_words:
        log("[System] Exit command detected")
        return {"should_continue": False}
    
    # Add user message to history
    new_message = Message(role="user", content=state.current_input)
    updated_messages = state.messages + [new_message]
    
    return {
        "messages": updated_messages,
        "should_continue": True
    }


def generate_response(state: ChatState) -> dict:
    """
    Node 3: Generate LLM response using full conversation history.
    
    This is where the magic happens - the LLM sees ALL previous
    messages, so it can maintain context across turns!
    """
    if not state.should_continue:
        return {}
    
    log(f"[LLM] Thinking...")
    
    # Get response from LLM with full history
    response_text = chat_with_llm(state.messages)
    
    # Add assistant message to history
    assistant_message = Message(role="assistant", content=response_text)
    updated_messages = state.messages + [assistant_message]
    
    log(f"Assistant: {response_text}")
    
    return {"messages": updated_messages}


# ============================================================
# Step 4: Define Routing Logic
# ============================================================

def should_continue(state: ChatState) -> Literal["continue", "end"]:
    """
    Conditional edge: decide whether to loop back or end.
    
    This is what creates the CYCLE in the graph!
    """
    if state.should_continue:
        return "continue"
    else:
        return "end"


# ============================================================
# Step 5: Build the Graph with a Cycle
# ============================================================

def create_chat_workflow():
    """
    Build the chat loop workflow.
    
    Key difference: we add an edge that goes BACK to get_input,
    creating a cycle in the graph.
    """
    builder = StateGraph(ChatState)
    
    # Add nodes
    builder.add_node("get_input", get_user_input)
    builder.add_node("process", process_message)
    builder.add_node("respond", generate_response)
    
    # Define the flow
    builder.add_edge(START, "get_input")
    builder.add_edge("get_input", "process")
    builder.add_edge("process", "respond")
    
    # Add the CONDITIONAL edge that creates the loop
    builder.add_conditional_edges(
        "respond",
        should_continue,
        {
            "continue": "get_input",  # Loop back! This creates the cycle
            "end": END
        }
    )
    
    return builder.compile()


# ============================================================
# Step 6: Run Interactive Chat
# ============================================================

def check_ollama() -> bool:
    """Check if Ollama is running."""
    try:
        client = get_client()
        client.models.list()
        return True
    except Exception:
        return False


def main():
    """Run the interactive chat loop."""
    
    log("=" * 50)
    log("LangGraph Example B: Multi-turn Chat Loop")
    log("=" * 50)
    
    log("\nChecking Ollama...")
    if not check_ollama():
        log("ERROR: Ollama is not running!")
        log("Start it with: ollama serve")
        return
    
    log("Ollama connected!")
    log(f"Model: {OLLAMA_MODEL}")
    log("-" * 50)
    
    # Create the workflow
    workflow = create_chat_workflow()
    
    # Start with empty state
    initial_state = ChatState()
    
    # Run the graph - it will loop until user says bye
    try:
        final_state = workflow.invoke(initial_state)
        
        log("\n" + "=" * 50)
        log(f"Chat ended after {final_state['turn_count']} turns")
        log(f"Total messages: {len(final_state['messages'])}")
        log("=" * 50)
        
    except KeyboardInterrupt:
        log("\n\nChat interrupted by user.")


def demo_mode():
    """
    Non-interactive demo for testing.
    Simulates a conversation without user input.
    """
    log("=" * 50)
    log("LangGraph Example B: Multi-turn Chat (Demo Mode)")
    log("=" * 50)
    
    log("\nChecking Ollama...")
    if not check_ollama():
        log("ERROR: Ollama is not running!")
        return
    
    log("Ollama connected!")
    log("-" * 50)
    
    # Simulate a conversation
    demo_inputs = [
        "Hi! What's your name?",
        "What did I just ask you?",  # Tests if LLM remembers context
        "bye"
    ]
    
    state = ChatState()
    
    for i, user_input in enumerate(demo_inputs, 1):
        log(f"\n[Turn {i}]")
        log(f"You: {user_input}")
        
        # Add user message
        state.messages.append(Message(role="user", content=user_input))
        
        # Check for exit
        if user_input.lower() in {"bye", "exit", "quit"}:
            log("[System] Exit command - ending chat")
            break
        
        # Get LLM response
        log("[LLM] Thinking...")
        response = chat_with_llm(state.messages)
        log(f"Assistant: {response}")
        
        # Add assistant message
        state.messages.append(Message(role="assistant", content=response))
    
    log("\n" + "=" * 50)
    log(f"Demo completed! {len(state.messages)} messages exchanged.")
    log("=" * 50)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--demo":
        demo_mode()
    else:
        main()

