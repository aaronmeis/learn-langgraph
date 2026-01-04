"""
LangGraph Examples - Flask Web Frontend

A simple web interface to explore all LangGraph examples.
Works on ARM Windows without pandas dependency!
"""

import warnings
# Suppress Pydantic V1 deprecation warnings for Python 3.14+
warnings.filterwarnings("ignore", category=UserWarning, module="langchain_core.*")

from flask import Flask, render_template_string, request, jsonify, session
from typing import Literal
import json
import re
import requests
from datetime import datetime
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from openai import OpenAI
import secrets

# ============================================================
# Configuration
# ============================================================

OLLAMA_BASE_URL = "http://localhost:11434/v1"
OLLAMA_MODEL = "llama3.2:1b"

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

def get_client():
    return OpenAI(base_url=OLLAMA_BASE_URL, api_key="ollama")

def check_ollama():
    try:
        get_client().models.list()
        return True
    except:
        return False

# ============================================================
# Example A: Simple Sentiment
# ============================================================

class SimpleState(BaseModel):
    user_input: str = ""
    word_count: int = 0
    sentiment: str = "neutral"
    response: str = ""

def simple_analyze(state: SimpleState) -> dict:
    text = state.user_input.lower()
    positive_words = {"good", "great", "love", "happy", "wonderful", "amazing", "excellent"}
    negative_words = {"bad", "terrible", "hate", "sad", "awful", "horrible", "angry"}
    words = set(text.split())
    pos = len(words & positive_words)
    neg = len(words & negative_words)
    if pos > neg:
        sentiment = "positive"
    elif neg > pos:
        sentiment = "negative"
    else:
        sentiment = "neutral"
    word_count = len(text.split())
    if sentiment == "positive":
        response = f"Great vibes! Your {word_count} words are full of positivity!"
    elif sentiment == "negative":
        response = f"I sense tough emotions in your {word_count} words. It's okay."
    else:
        response = f"Thanks for sharing {word_count} words. How can I help?"
    return {"sentiment": sentiment, "word_count": word_count, "response": response}

def create_simple_graph():
    builder = StateGraph(SimpleState)
    builder.add_node("analyze", simple_analyze)
    builder.add_edge(START, "analyze")
    builder.add_edge("analyze", END)
    return builder.compile()

# ============================================================
# Example B: LLM Sentiment
# ============================================================

class LLMState(BaseModel):
    user_input: str = ""
    sentiment: str = ""
    confidence: float = 0.0
    reasoning: str = ""

def llm_analyze(state: LLMState) -> dict:
    client = get_client()
    response = client.chat.completions.create(
        model=OLLAMA_MODEL, temperature=0,
        messages=[
            {"role": "system", "content": 'Analyze sentiment. Respond ONLY with JSON: {"sentiment": "positive/negative/neutral", "confidence": 0.0-1.0, "reasoning": "brief"}'},
            {"role": "user", "content": state.user_input}
        ]
    )
    try:
        match = re.search(r'\{.*\}', response.choices[0].message.content, re.DOTALL)
        if match:
            data = json.loads(match.group())
            return {
                "sentiment": data.get("sentiment", "neutral"),
                "confidence": data.get("confidence", 0.5),
                "reasoning": data.get("reasoning", "")
            }
    except:
        pass
    return {"sentiment": "neutral", "confidence": 0.5, "reasoning": "Could not parse"}
    
def create_llm_graph():
    builder = StateGraph(LLMState)
    builder.add_node("analyze", llm_analyze)
    builder.add_edge(START, "analyze")
    builder.add_edge("analyze", END)
    return builder.compile()

# ============================================================
# Example C & D: Chat
# ============================================================

class ChatState(BaseModel):
    messages: list = Field(default_factory=list)
    current_input: str = ""

def chat_respond(state: ChatState) -> dict:
    client = get_client()
    msgs = [{"role": "system", "content": "You are helpful. Keep responses to 1-2 sentences."}]
    msgs.extend(state.messages)
    msgs.append({"role": "user", "content": state.current_input})
    response = client.chat.completions.create(model=OLLAMA_MODEL, temperature=0.7, messages=msgs)
    new_msgs = state.messages + [
        {"role": "user", "content": state.current_input},
        {"role": "assistant", "content": response.choices[0].message.content}
    ]
    return {"messages": new_msgs}

def create_chat_graph():
    builder = StateGraph(ChatState)
    builder.add_node("respond", chat_respond)
    builder.add_edge(START, "respond")
    builder.add_edge("respond", END)
    return builder.compile()

# Persistent chat with checkpointer
persistent_checkpointer = MemorySaver()
def create_persistent_graph():
    builder = StateGraph(ChatState)
    builder.add_node("respond", chat_respond)
    builder.add_edge(START, "respond")
    builder.add_edge("respond", END)
    return builder.compile(checkpointer=persistent_checkpointer)

persistent_graph = create_persistent_graph()

# ============================================================
# Example E: Tool Agent
# ============================================================

def get_real_weather(city: str) -> str:
    """Fetch weather - tries real API first, falls back to mock data"""
    try:
        # Try wttr.in with longer timeout
        url = f"https://wttr.in/{city}?format=%C+%t"
        response = requests.get(url, timeout=10, headers={"User-Agent": "curl/7.0"})
        if response.status_code == 200 and len(response.text) < 100:
            weather = response.text.strip()
            if weather and "Unknown" not in weather:
                return f"{city}: {weather}"
    except:
        pass
    
    # Fallback to mock data
    mock_data = {
        "paris": "Partly cloudy, 59°F",
        "london": "Cloudy, 54°F",
        "tokyo": "Clear, 68°F",
        "new york": "Sunny, 72°F",
        "cedar rapids": "Cloudy, 45°F",
        "iowa": "Cloudy, 45°F",
    }
    city_lower = city.lower().strip()
    for key, value in mock_data.items():
        if key in city_lower:
            return f"{city}: {value} (cached)"
    return f"{city}: Weather data unavailable - try Paris, London, Tokyo, New York"

TOOLS = {
    "get_current_time": lambda: datetime.now().strftime("%A, %B %d, %Y at %I:%M %p"),
    "calculate": lambda expr: str(eval(expr)) if all(c in "0123456789+-*/().% " for c in expr) else "Error",
    "get_weather": get_real_weather
}

class AgentState(BaseModel):
    query: str = ""
    steps: list = Field(default_factory=list)
    tool_result: str = ""
    final_answer: str = ""
    tool_name: str = ""
    tool_args: str = ""
    iteration: int = 0

def agent_reason(state: AgentState) -> dict:
    steps = state.steps.copy()
    iteration = state.iteration + 1
    
    if iteration > 3:
        steps.append("Max iterations reached")
        return {"final_answer": state.tool_result or "Could not complete task.", "steps": steps, "iteration": iteration}
    
    if state.tool_result:
        steps.append("Got result, providing answer")
        return {"final_answer": f"The answer is: {state.tool_result}", "steps": steps, "iteration": iteration}
    
    client = get_client()
    response = client.chat.completions.create(
        model=OLLAMA_MODEL, temperature=0,
        messages=[
            {"role": "system", "content": 'Tools: get_current_time(), calculate(expression), get_weather(city). Respond ONLY JSON: {"thought":"...","tool":"name","args":"value"} OR {"thought":"...","answer":"final answer"}'},
            {"role": "user", "content": f"Query: {state.query}"}
        ]
    )
    
    try:
        match = re.search(r'\{.*\}', response.choices[0].message.content, re.DOTALL)
        if match:
            data = json.loads(match.group())
            steps.append(f"Thought: {data.get('thought', '')}")
            if "answer" in data:
                return {"final_answer": data["answer"], "steps": steps, "iteration": iteration}
            elif "tool" in data:
                return {"tool_name": data["tool"], "tool_args": str(data.get("args", "")), "steps": steps, "iteration": iteration}
    except:
        pass
    
    return {"final_answer": response.choices[0].message.content, "steps": steps, "iteration": iteration}

def agent_execute(state: AgentState) -> dict:
    if state.tool_name in TOOLS:
        steps = state.steps.copy()
        steps.append(f"Tool: {state.tool_name}({state.tool_args})")
        if state.tool_name == "get_current_time":
            result = TOOLS["get_current_time"]()
        elif state.tool_name == "calculate":
            result = TOOLS["calculate"](state.tool_args)
        else:
            result = TOOLS["get_weather"](state.tool_args)
        steps.append(f"Result: {result}")
        return {"tool_result": result, "tool_name": "", "steps": steps}
    return {}

def agent_route(state: AgentState):
    if state.final_answer:
        return "end"
    elif state.tool_name:
        return "execute"
    return "end"

def create_agent_graph():
    builder = StateGraph(AgentState)
    builder.add_node("reason", agent_reason)
    builder.add_node("execute", agent_execute)
    builder.add_edge(START, "reason")
    builder.add_conditional_edges("reason", agent_route, {"execute": "execute", "end": END})
    builder.add_edge("execute", "reason")
    return builder.compile()

# ============================================================
# HTML Template
# ============================================================

HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>LangGraph Examples</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { 
            font-family: 'Segoe UI', sans-serif;
            background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%);
            min-height: 100vh; color: #fff; padding: 20px;
        }
        .container { max-width: 900px; margin: 0 auto; }
        h1 { 
            text-align: center; font-size: 2.5em; margin-bottom: 10px;
            background: linear-gradient(90deg, #00d4ff, #7b2cbf);
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        }
        .status { text-align: center; margin-bottom: 20px; }
        .status.online { color: #00ff88; }
        .status.offline { color: #ff6b6b; }
        .tabs { display: flex; gap: 5px; margin-bottom: 20px; flex-wrap: wrap; }
        .tab { 
            padding: 12px 20px; background: rgba(255,255,255,0.1); border: none;
            color: #fff; cursor: pointer; border-radius: 8px 8px 0 0; font-size: 14px;
        }
        .tab:hover { background: rgba(255,255,255,0.2); }
        .tab.active { background: rgba(123,44,191,0.5); }
        .panel { 
            display: none; background: rgba(255,255,255,0.05); 
            padding: 25px; border-radius: 0 12px 12px 12px;
            border: 1px solid rgba(255,255,255,0.1);
        }
        .panel.active { display: block; }
        .panel h2 { margin-bottom: 10px; color: #00d4ff; }
        .panel p { margin-bottom: 15px; opacity: 0.8; }
        input[type="text"], select {
            width: 100%; padding: 12px; border: 1px solid rgba(255,255,255,0.2);
            background: rgba(0,0,0,0.3); color: #fff; border-radius: 8px;
            margin-bottom: 10px; font-size: 16px;
        }
        button {
            padding: 12px 25px; background: linear-gradient(90deg, #7b2cbf, #00d4ff);
            border: none; color: #fff; border-radius: 8px; cursor: pointer;
            font-size: 16px; margin-right: 10px;
        }
        button:hover { opacity: 0.9; }
        button.secondary { background: rgba(255,255,255,0.2); }
        .result {
            margin-top: 20px; padding: 15px; background: rgba(0,0,0,0.3);
            border-radius: 8px; border-left: 3px solid #7b2cbf;
        }
        .chat-msg { padding: 10px; margin: 5px 0; border-radius: 8px; }
        .chat-msg.user { background: rgba(0,212,255,0.2); border-left: 3px solid #00d4ff; }
        .chat-msg.assistant { background: rgba(123,44,191,0.2); border-left: 3px solid #7b2cbf; }
        .step { padding: 8px; background: rgba(255,193,7,0.2); border-radius: 5px; margin: 5px 0; font-family: monospace; }
        .metrics { display: flex; gap: 20px; margin: 15px 0; }
        .metric { text-align: center; padding: 15px; background: rgba(0,0,0,0.3); border-radius: 8px; flex: 1; }
        .metric-value { font-size: 1.8em; color: #00d4ff; }
        .metric-label { font-size: 0.9em; opacity: 0.7; }
        .tools { display: flex; gap: 10px; margin: 10px 0; }
        .tool-badge { padding: 5px 10px; background: rgba(255,255,255,0.1); border-radius: 15px; font-size: 0.9em; }
        #loading { display: none; color: #00d4ff; }
    </style>
</head>
<body>
    <div class="container">
        <h1>LangGraph Examples</h1>
        <div class="status {{ 'online' if ollama_status else 'offline' }}">
            {{ '&#9679; Ollama Connected' if ollama_status else '&#9679; Ollama Offline - Start with: ollama serve' }}
        </div>
        
        <div class="tabs">
            <button class="tab active" onclick="showTab('a')">A: Simple</button>
            <button class="tab" onclick="showTab('b')">B: LLM Sentiment</button>
            <button class="tab" onclick="showTab('c')">C: Chat</button>
            <button class="tab" onclick="showTab('d')">D: Persistent</button>
            <button class="tab" onclick="showTab('e')">E: Tool Agent</button>
        </div>
        
        <div id="panel-a" class="panel active">
            <h2>Simple Sentiment Analysis</h2>
            <p>Uses keyword matching - no LLM required!</p>
            <input type="text" id="input-a" placeholder="I love this amazing day!">
            <button onclick="runSimple()">Analyze</button>
            <div id="result-a" class="result" style="display:none"></div>
        </div>
        
        <div id="panel-b" class="panel">
            <h2>LLM Sentiment Analysis</h2>
            <p>Uses Ollama for intelligent analysis with reasoning!</p>
            <input type="text" id="input-b" placeholder="I got promoted but I'll miss my team">
            <button onclick="runLLM()">Analyze with LLM</button>
            <span id="loading">Analyzing...</span>
            <div id="result-b" class="result" style="display:none"></div>
        </div>
        
        <div id="panel-c" class="panel">
            <h2>Multi-turn Chat</h2>
            <p>Maintains conversation history - LLM remembers context!</p>
            <div id="chat-c" style="max-height:300px;overflow-y:auto;margin-bottom:10px"></div>
            <input type="text" id="input-c" placeholder="Hi! My name is Alice.">
            <button onclick="sendChat()">Send</button>
            <button class="secondary" onclick="clearChat()">Clear</button>
        </div>
        
        <div id="panel-d" class="panel">
            <h2>Persistent Conversations</h2>
            <p>Uses checkpointing - each thread has its own memory!</p>
            <select id="thread-select" onchange="loadThread()">
                <option value="alice-123">Thread: alice-123</option>
                <option value="bob-456">Thread: bob-456</option>
            </select>
            <div id="chat-d" style="max-height:300px;overflow-y:auto;margin-bottom:10px"></div>
            <input type="text" id="input-d" placeholder="Hi, I'm Alice!">
            <button onclick="sendPersistent()">Send</button>
            <button class="secondary" onclick="clearThread()">Clear Thread</button>
        </div>
        
        <div id="panel-e" class="panel">
            <h2>Tool-Calling Agent</h2>
            <p>ReAct pattern: Reason - Act - Observe. Now with REAL weather from the internet!</p>
            <div class="tools">
                <span class="tool-badge">get_current_time</span>
                <span class="tool-badge">calculate(expr)</span>
                <span class="tool-badge">get_weather(city)</span>
            </div>
            <input type="text" id="input-e" placeholder="What's the weather in Paris?">
            <button onclick="runAgent()">Run Agent</button>
            <div id="result-e" class="result" style="display:none"></div>
        </div>
    </div>
    
    <script>
        let chatMessages = [];
        let persistentMessages = {};
        
        function showTab(id) {
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
            event.target.classList.add('active');
            document.getElementById('panel-' + id).classList.add('active');
        }
        
        async function runSimple() {
            const input = document.getElementById('input-a').value;
            const res = await fetch('/api/simple', {
                method: 'POST', headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({input})
            });
            const data = await res.json();
            const emoji = {positive: '😊', negative: '😔', neutral: '😐'}[data.sentiment];
            document.getElementById('result-a').innerHTML = `
                <div class="metrics">
                    <div class="metric"><div class="metric-value">${emoji}</div><div class="metric-label">${data.sentiment}</div></div>
                    <div class="metric"><div class="metric-value">${data.word_count}</div><div class="metric-label">Words</div></div>
                </div>
                <p>${data.response}</p>`;
            document.getElementById('result-a').style.display = 'block';
        }
        
        async function runLLM() {
            const input = document.getElementById('input-b').value;
            document.getElementById('loading').style.display = 'inline';
            const res = await fetch('/api/llm', {
                method: 'POST', headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({input})
            });
            const data = await res.json();
            document.getElementById('loading').style.display = 'none';
            document.getElementById('result-b').innerHTML = `
                <div class="metrics">
                    <div class="metric"><div class="metric-value">${data.sentiment}</div><div class="metric-label">Sentiment</div></div>
                    <div class="metric"><div class="metric-value">${Math.round(data.confidence*100)}%</div><div class="metric-label">Confidence</div></div>
                </div>
                <p><strong>Reasoning:</strong> ${data.reasoning}</p>`;
            document.getElementById('result-b').style.display = 'block';
        }
        
        function renderChat(containerId, messages) {
            const container = document.getElementById(containerId);
            container.innerHTML = messages.map(m => 
                `<div class="chat-msg ${m.role}"><strong>${m.role === 'user' ? 'You' : 'Assistant'}:</strong> ${m.content}</div>`
            ).join('');
            container.scrollTop = container.scrollHeight;
        }
        
        async function sendChat() {
            const input = document.getElementById('input-c').value;
            if (!input) return;
            document.getElementById('input-c').value = '';
            const res = await fetch('/api/chat', {
                method: 'POST', headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({input, messages: chatMessages})
            });
            const data = await res.json();
            chatMessages = data.messages;
            renderChat('chat-c', chatMessages);
        }
        
        function clearChat() { chatMessages = []; renderChat('chat-c', []); }
        
        async function sendPersistent() {
            const input = document.getElementById('input-d').value;
            const thread = document.getElementById('thread-select').value;
            if (!input) return;
            document.getElementById('input-d').value = '';
            const res = await fetch('/api/persistent', {
                method: 'POST', headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({input, thread})
            });
            const data = await res.json();
            persistentMessages[thread] = data.messages;
            renderChat('chat-d', data.messages);
        }
        
        function loadThread() {
            const thread = document.getElementById('thread-select').value;
            renderChat('chat-d', persistentMessages[thread] || []);
        }
        
        function clearThread() {
            const thread = document.getElementById('thread-select').value;
            persistentMessages[thread] = [];
            renderChat('chat-d', []);
        }
        
        async function runAgent() {
            const input = document.getElementById('input-e').value;
            document.getElementById('result-e').innerHTML = '<p>Agent thinking...</p>';
            document.getElementById('result-e').style.display = 'block';
            const res = await fetch('/api/agent', {
                method: 'POST', headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({query: input})
            });
            const data = await res.json();
            document.getElementById('result-e').innerHTML = `
                <p><strong>Steps:</strong></p>
                ${data.steps.map(s => `<div class="step">${s}</div>`).join('')}
                <p style="margin-top:15px"><strong>Answer:</strong> ${data.answer}</p>`;
        }
    </script>
</body>
</html>
'''

# ============================================================
# Routes
# ============================================================

@app.route('/')
def index():
    return render_template_string(HTML, ollama_status=check_ollama())

@app.route('/api/simple', methods=['POST'])
def api_simple():
    data = request.json
    graph = create_simple_graph()
    result = graph.invoke({"user_input": data['input']})
    return jsonify(result)

@app.route('/api/llm', methods=['POST'])
def api_llm():
    data = request.json
    graph = create_llm_graph()
    result = graph.invoke({"user_input": data['input']})
    return jsonify(result)

@app.route('/api/chat', methods=['POST'])
def api_chat():
    data = request.json
    graph = create_chat_graph()
    result = graph.invoke({"messages": data.get('messages', []), "current_input": data['input']})
    return jsonify(result)

@app.route('/api/persistent', methods=['POST'])
def api_persistent():
    data = request.json
    thread_id = data.get('thread', 'default')
    
    if 'threads' not in session:
        session['threads'] = {}
    messages = session['threads'].get(thread_id, [])
    
    config = {"configurable": {"thread_id": thread_id}}
    result = persistent_graph.invoke({"messages": messages, "current_input": data['input']}, config=config)
    
    session['threads'][thread_id] = result['messages']
    session.modified = True
    
    return jsonify(result)

@app.route('/api/agent', methods=['POST'])
def api_agent():
    data = request.json
    graph = create_agent_graph()
    result = graph.invoke({"query": data['query']})
    return jsonify({"steps": result.get('steps', []), "answer": result.get('final_answer', '')})

if __name__ == '__main__':
    print("=" * 50)
    print("LangGraph Examples - Web UI")
    print("=" * 50)
    print(f"Ollama: {'Connected' if check_ollama() else 'Not running'}")
    print(f"Model: {OLLAMA_MODEL}")
    print("-" * 50)
    print("Open http://localhost:8080 in your browser")
    print("=" * 50)
    app.run(debug=True, host='127.0.0.1', port=8080)
