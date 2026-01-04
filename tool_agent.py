"""
LangGraph Example D: Tool-Calling Agent

This example demonstrates:
- Defining tools the LLM can use
- ReAct pattern (Reason → Act → Observe → Repeat)
- LLM deciding which tool to call
- Executing tools and feeding results back

Works with Ollama (llama3.2)!
"""

import warnings
# Suppress Pydantic V1 deprecation warnings for Python 3.14+
warnings.filterwarnings("ignore", category=UserWarning, module="langchain_core.*")

import sys
import json
import re
from typing import Literal
from datetime import datetime
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, START, END

from openai import OpenAI


# ============================================================
# Configuration
# ============================================================

OLLAMA_BASE_URL = "http://localhost:11434/v1"
OLLAMA_MODEL = "llama3.2:1b"


def log(message: str):
    print(message)
    sys.stdout.flush()


# ============================================================
# Step 1: Define Tools
# ============================================================

def get_current_time() -> str:
    """Get the current date and time."""
    now = datetime.now()
    return now.strftime("%A, %B %d, %Y at %I:%M %p")


def calculate(expression: str) -> str:
    """Safely evaluate a math expression."""
    try:
        # Only allow safe math operations
        allowed = set("0123456789+-*/().% ")
        if not all(c in allowed for c in expression):
            return "Error: Invalid characters in expression"
        result = eval(expression)
        return str(result)
    except Exception as e:
        return f"Error: {str(e)}"


def get_weather(city: str) -> str:
    """Get weather for a city (mock implementation)."""
    # Mock weather data - in production, call a real API
    weather_data = {
        "new york": "Sunny, 72°F (22°C)",
        "london": "Cloudy, 59°F (15°C)", 
        "tokyo": "Rainy, 68°F (20°C)",
        "paris": "Partly cloudy, 65°F (18°C)",
    }
    city_lower = city.lower().strip()
    return weather_data.get(city_lower, f"Weather data not available for {city}")


# Tool registry
TOOLS = {
    "get_current_time": {
        "function": get_current_time,
        "description": "Get the current date and time. No parameters needed.",
        "parameters": []
    },
    "calculate": {
        "function": calculate,
        "description": "Calculate a math expression. Parameter: expression (string)",
        "parameters": ["expression"]
    },
    "get_weather": {
        "function": get_weather,
        "description": "Get weather for a city. Parameter: city (string)",
        "parameters": ["city"]
    }
}


# ============================================================
# Step 2: Define Agent State
# ============================================================

class AgentState(BaseModel):
    """State for the tool-calling agent."""
    user_query: str = Field(default="", description="Original user question")
    thought: str = Field(default="", description="Agent's reasoning")
    tool_name: str = Field(default="", description="Tool to call (or 'none')")
    tool_args: dict = Field(default_factory=dict, description="Tool arguments")
    tool_result: str = Field(default="", description="Result from tool")
    final_answer: str = Field(default="", description="Final response to user")
    step_count: int = Field(default=0, description="Number of reasoning steps")


# ============================================================
# Step 3: Ollama Client with Tool Prompting
# ============================================================

def get_client() -> OpenAI:
    return OpenAI(base_url=OLLAMA_BASE_URL, api_key="ollama")


def build_tool_prompt() -> str:
    """Build a prompt describing available tools."""
    tool_descriptions = []
    for name, info in TOOLS.items():
        params = ", ".join(info["parameters"]) if info["parameters"] else "none"
        tool_descriptions.append(f"- {name}: {info['description']}")
    
    return "\n".join(tool_descriptions)


def ask_agent(query: str, tool_result: str = None) -> dict:
    """
    Ask the agent to reason about the query and decide on action.
    Returns: {thought, tool_name, tool_args} or {thought, final_answer}
    """
    client = get_client()
    
    tools_desc = build_tool_prompt()
    
    system_prompt = f"""You are a helpful assistant with access to tools.

Available tools:
{tools_desc}

For each query, think step by step:
1. THOUGHT: Explain your reasoning
2. ACTION: Either call a tool OR provide final answer

Respond in this EXACT JSON format (no other text):

If you need to use a tool:
{{"thought": "your reasoning", "tool": "tool_name", "args": {{"param": "value"}}}}

If you have the final answer:
{{"thought": "your reasoning", "answer": "your final answer to the user"}}

Examples:
- User asks time → {{"thought": "User wants current time", "tool": "get_current_time", "args": {{}}}}
- User asks 5+3 → {{"thought": "Need to calculate", "tool": "calculate", "args": {{"expression": "5+3"}}}}
- User asks weather in Paris → {{"thought": "Need weather data", "tool": "get_weather", "args": {{"city": "Paris"}}}}
- After getting tool result → {{"thought": "I have the answer now", "answer": "The time is..."}}"""

    messages = [{"role": "system", "content": system_prompt}]
    
    if tool_result:
        messages.append({"role": "user", "content": query})
        messages.append({"role": "assistant", "content": f"Tool returned: {tool_result}"})
        messages.append({"role": "user", "content": "Now provide the final answer based on this result."})
    else:
        messages.append({"role": "user", "content": query})
    
    response = client.chat.completions.create(
        model=OLLAMA_MODEL,
        temperature=0,
        messages=messages,
    )
    
    content = response.choices[0].message.content.strip()
    
    # Extract JSON from response
    try:
        # Try to find JSON in the response
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
        return json.loads(content)
    except:
        # Fallback: treat as final answer
        return {"thought": "Providing direct answer", "answer": content}


# ============================================================
# Step 4: Define Node Functions
# ============================================================

def reason(state: AgentState) -> dict:
    """
    Node 1: Agent reasons about what to do.
    Decides whether to use a tool or provide final answer.
    """
    log(f"\n[Step {state.step_count + 1}] Reasoning...")
    
    # Ask agent what to do
    if state.tool_result:
        log(f"[Agent] Received tool result: {state.tool_result}")
        result = ask_agent(state.user_query, state.tool_result)
    else:
        result = ask_agent(state.user_query)
    
    thought = result.get("thought", "")
    log(f"[Thought] {thought}")
    
    # Check if agent wants to use a tool or give final answer
    if "answer" in result:
        return {
            "thought": thought,
            "final_answer": result["answer"],
            "tool_name": "none",
            "step_count": state.step_count + 1
        }
    elif "tool" in result:
        tool_name = result["tool"]
        tool_args = result.get("args", {})
        log(f"[Action] Calling tool: {tool_name} with args: {tool_args}")
        return {
            "thought": thought,
            "tool_name": tool_name,
            "tool_args": tool_args,
            "step_count": state.step_count + 1
        }
    else:
        # Fallback
        return {
            "thought": thought,
            "final_answer": "I'm not sure how to help with that.",
            "tool_name": "none",
            "step_count": state.step_count + 1
        }


def execute_tool(state: AgentState) -> dict:
    """
    Node 2: Execute the selected tool.
    """
    if state.tool_name == "none" or state.tool_name not in TOOLS:
        return {}
    
    log(f"[Executing] {state.tool_name}...")
    
    tool_info = TOOLS[state.tool_name]
    func = tool_info["function"]
    
    # Call the tool with appropriate arguments
    if state.tool_name == "get_current_time":
        result = func()
    elif state.tool_name == "calculate":
        result = func(state.tool_args.get("expression", ""))
    elif state.tool_name == "get_weather":
        result = func(state.tool_args.get("city", ""))
    else:
        result = "Unknown tool"
    
    log(f"[Result] {result}")
    
    return {"tool_result": result}


def format_response(state: AgentState) -> dict:
    """
    Node 3: Format the final response.
    """
    if not state.final_answer:
        return {}
    
    log(f"\n[Final Answer] {state.final_answer}")
    return {}


# ============================================================
# Step 5: Define Routing
# ============================================================

def should_continue(state: AgentState) -> Literal["execute", "respond", "reason"]:
    """
    Route based on agent's decision:
    - If tool selected → execute it
    - If final answer ready → respond
    - If need more reasoning → loop back
    """
    if state.final_answer:
        return "respond"
    elif state.tool_name and state.tool_name != "none":
        return "execute"
    else:
        return "respond"


def after_tool(state: AgentState) -> Literal["reason"]:
    """After executing tool, go back to reasoning."""
    return "reason"


# ============================================================
# Step 6: Build the Agent Graph
# ============================================================

def create_agent():
    """
    Build the ReAct agent graph.
    
    Structure:
        START → reason ──→ execute_tool ──→ reason (loop)
                   │                            
                   └──→ format_response → END
    """
    builder = StateGraph(AgentState)
    
    # Add nodes
    builder.add_node("reason", reason)
    builder.add_node("execute", execute_tool)
    builder.add_node("respond", format_response)
    
    # Entry point
    builder.add_edge(START, "reason")
    
    # After reasoning, decide what to do
    builder.add_conditional_edges(
        "reason",
        should_continue,
        {
            "execute": "execute",
            "respond": "respond",
            "reason": "reason"
        }
    )
    
    # After executing tool, go back to reason
    builder.add_edge("execute", "reason")
    
    # Respond leads to end
    builder.add_edge("respond", END)
    
    return builder.compile()


# ============================================================
# Step 7: Run Demo
# ============================================================

def check_ollama() -> bool:
    try:
        get_client().models.list()
        return True
    except:
        return False


def main():
    log("=" * 55)
    log("LangGraph Example D: Tool-Calling Agent")
    log("=" * 55)
    
    log("\nChecking Ollama...")
    if not check_ollama():
        log("ERROR: Ollama not running!")
        return
    log("Ollama connected!")
    
    log("\nAvailable Tools:")
    for name, info in TOOLS.items():
        log(f"  - {name}: {info['description']}")
    
    # Create agent
    agent = create_agent()
    
    # Test queries
    test_queries = [
        "What time is it?",
        "What is 25 * 4 + 10?",
        "What's the weather in Tokyo?",
    ]
    
    for query in test_queries:
        log("\n" + "=" * 55)
        log(f"USER: {query}")
        log("-" * 55)
        
        result = agent.invoke({"user_query": query})
        
        log(f"\nCompleted in {result['step_count']} step(s)")
    
    log("\n" + "=" * 55)
    log("Agent demo complete!")
    log("=" * 55)


if __name__ == "__main__":
    main()

