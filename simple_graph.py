"""
Simple LangGraph Example with Pydantic State Management

This example demonstrates:
- Defining state with Pydantic BaseModel
- Creating nodes that process state
- Adding edges to connect nodes
- Conditional routing based on state
"""

from typing import Literal
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, START, END


# ============================================================
# Step 1: Define the State using Pydantic
# ============================================================

class WorkflowState(BaseModel):
    """
    Pydantic model representing the state that flows through the graph.
    Each node receives and returns this state (or updates to it).
    """
    user_input: str = Field(default="", description="The user's input text")
    processed_input: str = Field(default="", description="Cleaned/processed input")
    word_count: int = Field(default=0, description="Number of words in input")
    sentiment: Literal["positive", "negative", "neutral"] = Field(
        default="neutral", description="Detected sentiment"
    )
    response: str = Field(default="", description="Final response to user")


# ============================================================
# Step 2: Define Node Functions
# ============================================================

def process_input(state: WorkflowState) -> dict:
    """
    Node 1: Process the raw user input.
    - Strips whitespace
    - Counts words
    """
    cleaned = state.user_input.strip()
    words = cleaned.split()
    
    print(f"[Input] Processing: '{cleaned}'")
    print(f"   Word count: {len(words)}")
    
    return {
        "processed_input": cleaned,
        "word_count": len(words)
    }


def analyze_sentiment(state: WorkflowState) -> dict:
    """
    Node 2: Simple sentiment analysis based on keywords.
    (In a real app, you'd use an LLM or ML model here)
    """
    text = state.processed_input.lower()
    
    positive_words = {"good", "great", "excellent", "happy", "love", "wonderful", "amazing"}
    negative_words = {"bad", "terrible", "awful", "sad", "hate", "horrible", "angry"}
    
    words = set(text.split())
    
    positive_score = len(words & positive_words)
    negative_score = len(words & negative_words)
    
    if positive_score > negative_score:
        sentiment = "positive"
    elif negative_score > positive_score:
        sentiment = "negative"
    else:
        sentiment = "neutral"
    
    print(f"[Sentiment] Detected: {sentiment}")
    
    return {"sentiment": sentiment}


def generate_positive_response(state: WorkflowState) -> dict:
    """Node 3a: Generate response for positive sentiment."""
    response = f"That's wonderful! I love your positive energy. You shared {state.word_count} words of joy!"
    print(f"[Response] Generating positive response")
    return {"response": response}


def generate_negative_response(state: WorkflowState) -> dict:
    """Node 3b: Generate response for negative sentiment."""
    response = f"I hear you. It sounds like things are tough. Remember, it's okay to feel this way."
    print(f"[Response] Generating supportive response")
    return {"response": response}


def generate_neutral_response(state: WorkflowState) -> dict:
    """Node 3c: Generate response for neutral sentiment."""
    response = f"Thanks for sharing! You wrote {state.word_count} words. How can I help you further?"
    print(f"[Response] Generating neutral response")
    return {"response": response}


# ============================================================
# Step 3: Define Routing Logic
# ============================================================

def route_by_sentiment(state: WorkflowState) -> Literal["positive", "negative", "neutral"]:
    """
    Conditional routing function.
    Returns the name of the next node based on sentiment.
    """
    return state.sentiment


# ============================================================
# Step 4: Build the Graph
# ============================================================

def create_workflow() -> StateGraph:
    """
    Build and compile the LangGraph workflow.
    
    Graph structure:
    
        START
          │
          ▼
      process_input
          │
          ▼
    analyze_sentiment
          │
          ├─── positive ──► generate_positive_response ──┐
          │                                               │
          ├─── negative ──► generate_negative_response ──┤
          │                                               │
          └─── neutral ───► generate_neutral_response ───┘
                                                          │
                                                          ▼
                                                         END
    """
    # Initialize the graph with our Pydantic state model
    builder = StateGraph(WorkflowState)
    
    # Add all nodes
    builder.add_node("process_input", process_input)
    builder.add_node("analyze_sentiment", analyze_sentiment)
    builder.add_node("positive", generate_positive_response)
    builder.add_node("negative", generate_negative_response)
    builder.add_node("neutral", generate_neutral_response)
    
    # Define the flow
    builder.add_edge(START, "process_input")
    builder.add_edge("process_input", "analyze_sentiment")
    
    # Add conditional routing based on sentiment
    builder.add_conditional_edges(
        "analyze_sentiment",
        route_by_sentiment,
        {
            "positive": "positive",
            "negative": "negative",
            "neutral": "neutral"
        }
    )
    
    # All response nodes lead to END
    builder.add_edge("positive", END)
    builder.add_edge("negative", END)
    builder.add_edge("neutral", END)
    
    # Compile and return the graph
    return builder.compile()


# ============================================================
# Step 5: Run the Workflow
# ============================================================

def main():
    """Run the workflow with different inputs to demonstrate routing."""
    
    # Create the compiled workflow
    workflow = create_workflow()
    
    # Test inputs with different sentiments
    test_inputs = [
        "I love this amazing day! Everything is wonderful!",
        "This is terrible. I hate when bad things happen.",
        "The weather is cloudy today. I might go for a walk.",
    ]
    
    print("=" * 60)
    print("LangGraph Simple Example - Sentiment Router")
    print("=" * 60)
    
    for i, user_text in enumerate(test_inputs, 1):
        print(f"\n{'─' * 60}")
        print(f"Test {i}: \"{user_text}\"")
        print("─" * 60)
        
        # Create initial state with Pydantic
        initial_state = WorkflowState(user_input=user_text)
        
        # Invoke the workflow
        result = workflow.invoke(initial_state)
        
        print(f"\n[Final Response]: {result['response']}")
    
    print(f"\n{'=' * 60}")
    print("All tests completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()

