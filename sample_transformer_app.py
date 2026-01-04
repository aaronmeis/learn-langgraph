"""
Sample Requirements Transformer - Flask Web Application
========================================================

A web interface for transforming sample requirements documents with a dropdown
selector. Users can select from pre-written sample requirements files.

Run: python sample_transformer_app.py
Open: http://localhost:5002
"""

import warnings
# Suppress Pydantic V1 deprecation warnings for Python 3.14+
warnings.filterwarnings("ignore", category=UserWarning, module="langchain_core.*")

import json
import os
import platform
import re
import struct
import threading
import time
import uuid
from datetime import datetime
from flask import Flask, render_template_string, jsonify, request, session
from openai import OpenAI

app = Flask(__name__)
app.secret_key = "sample-transformer-secret-key-2025"

# ============================================================
# Environment Detection
# ============================================================

def detect_environment():
    """Detect the current system environment."""
    env_info = {
        "os": platform.system(),
        "os_version": platform.version(),
        "os_release": platform.release(),
        "architecture": platform.machine(),
        "processor": platform.processor(),
        "python_version": platform.python_version(),
        "is_windows": platform.system() == "Windows",
        "is_linux": platform.system() == "Linux",
        "is_macos": platform.system() == "Darwin",
        "is_arm": False,
        "is_x86": False,
        "is_64bit": struct.calcsize("P") * 8 == 64,
        "pointer_size": struct.calcsize("P") * 8
    }
    
    arch_lower = env_info["architecture"].lower()
    if any(arm in arch_lower for arm in ["arm", "aarch"]):
        env_info["is_arm"] = True
        env_info["arch_family"] = "ARM"
    elif any(x86 in arch_lower for x86 in ["x86", "amd64", "i386", "i686"]):
        env_info["is_x86"] = True
        env_info["arch_family"] = "x86"
    else:
        env_info["arch_family"] = "Unknown"
    
    os_name = env_info["os"]
    if env_info["is_windows"]:
        os_name = f"Windows {env_info['os_release']}"
    elif env_info["is_linux"]:
        try:
            import distro
            os_name = f"{distro.name()} {distro.version()}"
        except ImportError:
            os_name = f"Linux {env_info['os_release']}"
    elif env_info["is_macos"]:
        os_name = f"macOS {env_info['os_release']}"
    
    arch_bits = "64-bit" if env_info["is_64bit"] else "32-bit"
    env_info["summary"] = f"{os_name} | {env_info['arch_family']} ({env_info['architecture']}) | {arch_bits}"
    
    return env_info

SYSTEM_ENV = detect_environment()

def generate_run_id():
    """Generate a unique run ID (short UUID)."""
    return str(uuid.uuid4())[:8]

# ============================================================
# Configuration
# ============================================================

OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434/v1")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.2:1b")

def get_client():
    return OpenAI(base_url=OLLAMA_BASE_URL, api_key="ollama")

# ============================================================
# Sample Requirements File Management
# ============================================================

REQUIREMENTS_DIR = "requirements"

def get_sample_files():
    """Get list of sample requirements files."""
    if not os.path.exists(REQUIREMENTS_DIR):
        return []
    
    files = []
    for filename in os.listdir(REQUIREMENTS_DIR):
        if filename.endswith('.md') and filename != 'README.md':
            filepath = os.path.join(REQUIREMENTS_DIR, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # Extract title from first line or filename
                    first_line = content.split('\n')[0].strip('#').strip()
                    title = first_line if first_line else filename.replace('.md', '').replace('_', ' ').title()
                    files.append({
                        "filename": filename,
                        "filepath": filepath,
                        "title": title,
                        "size": len(content)
                    })
            except Exception as e:
                print(f"Error reading {filename}: {e}")
    
    return sorted(files, key=lambda x: x['filename'])

def load_sample_file(filename):
    """Load content of a sample requirements file."""
    filepath = os.path.join(REQUIREMENTS_DIR, filename)
    if not os.path.exists(filepath):
        return None
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"Error loading {filename}: {e}")
        return None

# ============================================================
# Pipeline State (stored in memory for demo)
# ============================================================

def create_initial_state():
    """Create a fresh pipeline state with new run ID."""
    return {
        "status": "idle",  # idle, running, waiting_review, waiting_approval, complete, error
        "run_id": generate_run_id(),
        "environment": SYSTEM_ENV,
        "started_at": None,
        "completed_at": None,
        "current_step": 0,
        "selected_file": None,
        "steps": [
            {"id": 1, "name": "Load Source", "status": "pending", "details": ""},
            {"id": 2, "name": "Load Template", "status": "pending", "details": ""},
            {"id": 3, "name": "Analyze Mapping", "status": "pending", "details": ""},
            {"id": 4, "name": "Human Review", "status": "pending", "details": "", "hitl": True},
            {"id": 5, "name": "Transform", "status": "pending", "details": ""},
            {"id": 6, "name": "Validate", "status": "pending", "details": ""},
            {"id": 7, "name": "Human Approval", "status": "pending", "details": "", "hitl": True},
            {"id": 8, "name": "Generate Output", "status": "pending", "details": ""},
        ],
        "source_doc": {},
        "template": {},
        "mapping": {},
        "mapping_explanation": "",
        "transformed": {},
        "validation": {},
        "final_output": "",
        "output_file": "",
        "logs": []
    }

pipeline_state = create_initial_state()

# ============================================================
# Target Template (IEEE 830 format)
# ============================================================

TARGET_TEMPLATE = """# Software Requirements Specification (IEEE 830 Format)

Version: 1.0
Date: {date}
Author: Requirements Engineering Team

## 1. Introduction

### 1.1 Purpose
[Purpose of the document]

### 1.2 Scope
[Scope of the project]

### 1.3 Definitions, Acronyms, and Abbreviations
[Glossary]

### 1.4 References
[References]

### 1.5 Overview
[Overview of the document]

## 2. Overall Description

### 2.1 Product Perspective
[System context]

### 2.2 Product Functions
[High-level functions]

### 2.3 User Classes and Characteristics
[User types]

### 2.4 Operating Environment
[Platform requirements]

### 2.5 Design and Implementation Constraints
[Constraints]

### 2.6 User Documentation
[Documentation requirements]

### 2.7 Assumptions and Dependencies
[Assumptions]

## 3. System Features

### 3.1 [Feature 1]
#### 3.1.1 Description and Priority
[Description]

#### 3.1.2 Stimulus/Response Sequences
[User actions and system responses]

#### 3.1.3 Functional Requirements
- REQ-001: [Requirement]
- REQ-002: [Requirement]

### 3.2 [Feature 2]
[Similar structure]

## 4. External Interface Requirements

### 4.1 User Interfaces
[UI requirements]

### 4.2 Hardware Interfaces
[Hardware requirements]

### 4.3 Software Interfaces
[Software integrations]

### 4.4 Communications Interfaces
[Network/API requirements]

## 5. Non-Functional Requirements

### 5.1 Performance Requirements
[Performance specs]

### 5.2 Safety Requirements
[Safety considerations]

### 5.3 Security Requirements
[Security requirements]

### 5.4 Software Quality Attributes
[Quality attributes]

## 6. Other Requirements

### 6.1 Appendices
[Additional information]
"""

# ============================================================
# Helper Functions
# ============================================================

def add_log(message):
    """Add a log message to the pipeline state."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    pipeline_state["logs"].append(f"[{timestamp}] {message}")
    if len(pipeline_state["logs"]) > 100:
        pipeline_state["logs"] = pipeline_state["logs"][-100:]

# ============================================================
# Pipeline Steps
# ============================================================

def step1_load_source():
    """Step 1: Load the selected source document."""
    add_log("Step 1: Loading source document...")
    pipeline_state["steps"][0]["status"] = "running"
    
    selected_file = pipeline_state.get("selected_file")
    if not selected_file:
        pipeline_state["steps"][0]["status"] = "error"
        pipeline_state["status"] = "error"
        add_log("ERROR: No file selected")
        return False
    
    content = load_sample_file(selected_file)
    if not content:
        pipeline_state["steps"][0]["status"] = "error"
        pipeline_state["status"] = "error"
        add_log(f"ERROR: Could not load file {selected_file}")
        return False
    
    pipeline_state["source_doc"] = {
        "filename": selected_file,
        "content": content,
        "size": len(content)
    }
    
    pipeline_state["steps"][0]["status"] = "complete"
    pipeline_state["steps"][0]["details"] = f"Loaded {selected_file} ({len(content)} chars)"
    add_log(f"Loaded source document: {selected_file}")
    return True

def step2_load_template():
    """Step 2: Load the target template."""
    add_log("Step 2: Loading target template...")
    pipeline_state["steps"][1]["status"] = "running"
    
    pipeline_state["template"] = {
        "format": "IEEE 830",
        "content": TARGET_TEMPLATE
    }
    
    pipeline_state["steps"][1]["status"] = "complete"
    pipeline_state["steps"][1]["details"] = "IEEE 830 format template loaded"
    add_log("Target template loaded (IEEE 830 format)")
    return True

def step3_analyze_mapping():
    """Step 3: Analyze mapping between source and target."""
    add_log("Step 3: Analyzing mapping...")
    pipeline_state["steps"][2]["status"] = "running"
    
    source_content = pipeline_state["source_doc"]["content"]
    
    # Use LLM to analyze the mapping
    client = get_client()
    prompt = f"""Analyze the following requirements document and explain how it maps to IEEE 830 format.

Source Document:
{source_content[:2000]}...

Provide a mapping analysis explaining:
1. Key features and functions identified
2. How they map to IEEE 830 sections
3. Any missing information that needs to be inferred
4. Recommendations for the transformation

Keep the analysis concise but comprehensive."""

    try:
        response = client.chat.completions.create(
            model=OLLAMA_MODEL,
            temperature=0.3,
            messages=[
                {"role": "system", "content": "You are a requirements engineering expert specializing in IEEE 830 format conversion."},
                {"role": "user", "content": prompt}
            ]
        )
        
        analysis = response.choices[0].message.content
        pipeline_state["mapping_explanation"] = analysis
        pipeline_state["steps"][2]["status"] = "complete"
        pipeline_state["steps"][2]["details"] = "Mapping analysis completed"
        add_log("Mapping analysis completed")
        
        # After analysis, set up human review checkpoint
        pipeline_state["status"] = "waiting_review"
        pipeline_state["steps"][3]["status"] = "waiting"
        add_log("Waiting for human review of mapping analysis...")
        
        return True
    except Exception as e:
        pipeline_state["steps"][2]["status"] = "error"
        pipeline_state["status"] = "error"
        add_log(f"ERROR in mapping analysis: {str(e)}")
        return False

def step5_transform():
    """Step 5: Transform the document."""
    add_log("Step 5: Transforming document...")
    pipeline_state["steps"][4]["status"] = "running"
    
    source_content = pipeline_state["source_doc"]["content"]
    mapping = pipeline_state["mapping_explanation"]
    
    client = get_client()
    prompt = f"""Transform the following requirements document into IEEE 830 format.

Source Document:
{source_content}

Mapping Analysis:
{mapping}

Transform this into a complete IEEE 830 Software Requirements Specification. Fill in all sections appropriately based on the source content. Use the template structure provided and ensure all requirements are properly numbered (REQ-001, REQ-002, etc.)."""

    try:
        response = client.chat.completions.create(
            model=OLLAMA_MODEL,
            temperature=0.2,
            messages=[
                {"role": "system", "content": "You are a requirements engineering expert. Transform requirements documents into IEEE 830 format with precision and completeness."},
                {"role": "user", "content": prompt}
            ]
        )
        
        transformed = response.choices[0].message.content
        pipeline_state["transformed"] = {
            "content": transformed,
            "format": "IEEE 830"
        }
        pipeline_state["steps"][4]["status"] = "complete"
        pipeline_state["steps"][4]["details"] = "Document transformed to IEEE 830"
        add_log("Document transformation completed")
        return True
    except Exception as e:
        pipeline_state["steps"][4]["status"] = "error"
        pipeline_state["status"] = "error"
        add_log(f"ERROR in transformation: {str(e)}")
        return False

def step6_validate():
    """Step 6: Validate the transformed document."""
    add_log("Step 6: Validating transformed document...")
    pipeline_state["steps"][5]["status"] = "running"
    
    transformed = pipeline_state["transformed"]["content"]
    
    client = get_client()
    prompt = f"""Validate the following IEEE 830 requirements document for completeness and correctness.

Transformed Document:
{transformed[:3000]}...

Check for:
1. All required IEEE 830 sections are present
2. Requirements are properly numbered
3. No missing critical information
4. Formatting is correct

Provide validation feedback."""

    try:
        response = client.chat.completions.create(
            model=OLLAMA_MODEL,
            temperature=0.1,
            messages=[
                {"role": "system", "content": "You are a quality assurance expert for requirements documents."},
                {"role": "user", "content": prompt}
            ]
        )
        
        validation = response.choices[0].message.content
        pipeline_state["validation"] = {
            "feedback": validation,
            "status": "validated"
        }
        pipeline_state["steps"][5]["status"] = "complete"
        pipeline_state["steps"][5]["details"] = "Validation completed"
        add_log("Document validation completed")
        
        # After validation, set up human approval checkpoint
        pipeline_state["status"] = "waiting_approval"
        pipeline_state["steps"][6]["status"] = "waiting"
        add_log("Waiting for human approval...")
        
        return True
    except Exception as e:
        pipeline_state["steps"][5]["status"] = "error"
        pipeline_state["status"] = "error"
        add_log(f"ERROR in validation: {str(e)}")
        return False

def step8_generate():
    """Step 8: Generate final output file."""
    add_log("Step 8: Generating output file...")
    pipeline_state["steps"][7]["status"] = "running"
    
    transformed = pipeline_state["transformed"]["content"]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_id = pipeline_state["run_id"]
    source_filename = pipeline_state["selected_file"].replace('.md', '')
    
    output_filename = f"transformed_ieee830_{timestamp}_{run_id}.md"
    output_path = os.path.join("_outputs", output_filename)
    
    # Ensure _outputs directory exists
    os.makedirs("_outputs", exist_ok=True)
    
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(transformed)
        
        pipeline_state["final_output"] = transformed
        pipeline_state["output_file"] = output_filename
        pipeline_state["steps"][7]["status"] = "complete"
        pipeline_state["steps"][7]["details"] = f"Output saved: {output_filename}"
        add_log(f"Output file generated: {output_filename}")
        return True
    except Exception as e:
        pipeline_state["steps"][7]["status"] = "error"
        pipeline_state["status"] = "error"
        add_log(f"ERROR generating output: {str(e)}")
        return False

# ============================================================
# Pipeline Execution
# ============================================================

def run_pipeline_step(step_num):
    """Run a specific pipeline step."""
    if step_num == 1:
        return step1_load_source()
    elif step_num == 2:
        return step2_load_template()
    elif step_num == 3:
        return step3_analyze_mapping()
    elif step_num == 4:
        # Human review checkpoint
        pipeline_state["status"] = "waiting_review"
        pipeline_state["steps"][3]["status"] = "waiting"
        add_log("Waiting for human review...")
        return True
    elif step_num == 5:
        return step5_transform()
    elif step_num == 6:
        return step6_validate()
    elif step_num == 7:
        # Human approval checkpoint
        pipeline_state["status"] = "waiting_approval"
        pipeline_state["steps"][6]["status"] = "waiting"
        add_log("Waiting for human approval...")
        return True
    elif step_num == 8:
        return step8_generate()
    return False

def run_pipeline_async():
    """Run the pipeline asynchronously."""
    steps = [1, 2, 3, 5, 6, 8]  # Skip 4 and 7 - they're HITL checkpoints
    
    for step_num in steps:
        # Check if we should stop (error or waiting for human input)
        if pipeline_state["status"] in ["error", "waiting_review", "waiting_approval"]:
            break
        
        success = run_pipeline_step(step_num)
        if not success:
            pipeline_state["status"] = "error"
            break
        
        # After step 3, check if we're now waiting for review
        if step_num == 3 and pipeline_state["status"] == "waiting_review":
            break  # Stop here, waiting for human review
        
        # After step 6, check if we're now waiting for approval
        if step_num == 6 and pipeline_state["status"] == "waiting_approval":
            break  # Stop here, waiting for human approval
        
        time.sleep(0.5)  # Small delay for UI updates
    
    # Only mark as complete if we finished all steps without waiting
    if pipeline_state["status"] == "running":
        pipeline_state["status"] = "complete"
        pipeline_state["completed_at"] = datetime.now().isoformat()
        add_log("Pipeline completed successfully!")

def continue_after_review():
    """Continue pipeline after human review approval."""
    pipeline_state["steps"][3]["status"] = "complete"
    pipeline_state["steps"][3]["details"] = "Human review approved"
    add_log("Human review approved, continuing...")
    
    # Continue with remaining steps
    for step_num in [5, 6, 7, 8]:
        if pipeline_state["status"] == "error":
            break
        
        if step_num == 7:
            # Wait for human approval
            break
        
        success = run_pipeline_step(step_num)
        if not success:
            pipeline_state["status"] = "error"
            break
        
        time.sleep(0.5)
    
    if pipeline_state["status"] not in ["waiting_approval", "error"]:
        pipeline_state["status"] = "complete"
        pipeline_state["completed_at"] = datetime.now().isoformat()
        add_log("Pipeline completed successfully!")

def continue_after_approval():
    """Continue pipeline after human approval."""
    pipeline_state["steps"][6]["status"] = "complete"
    pipeline_state["steps"][6]["details"] = "Human approval granted"
    pipeline_state["status"] = "running"  # Set back to running to continue
    add_log("Human approval granted, generating output...")
    
    success = run_pipeline_step(8)
    if success:
        pipeline_state["status"] = "complete"
        pipeline_state["completed_at"] = datetime.now().isoformat()
        add_log("Pipeline completed successfully!")
        add_log(f"Output file: {pipeline_state.get('output_file', 'N/A')}")
    else:
        pipeline_state["status"] = "error"
        add_log("ERROR: Failed to generate output file")

# ============================================================
# HTML Template
# ============================================================

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sample Requirements Transformer</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            color: #e0e0e0;
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 1400px;
            margin: 0 auto;
            background: #1e1e2e;
            border-radius: 12px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.5);
            overflow: hidden;
            border: 1px solid #333;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }
        .header h1 { font-size: 2.5em; margin-bottom: 10px; }
        .header p { opacity: 0.9; font-size: 1.1em; }
        .controls {
            padding: 30px;
            background: #252538;
            border-bottom: 2px solid #3a3a4a;
        }
        .file-selector {
            margin-bottom: 20px;
        }
        .file-selector label {
            display: block;
            font-weight: 600;
            margin-bottom: 10px;
            color: #e0e0e0;
        }
        .file-selector select {
            width: 100%;
            padding: 12px;
            font-size: 1em;
            border: 2px solid #4a4a5a;
            border-radius: 8px;
            background: #2a2a3a;
            color: #e0e0e0;
            cursor: pointer;
        }
        .file-selector select:focus {
            outline: none;
            border-color: #667eea;
            background: #2f2f3f;
        }
        .file-selector option {
            background: #2a2a3a;
            color: #e0e0e0;
        }
        .file-info {
            margin-top: 10px;
            padding: 10px;
            background: #1a3a5a;
            border-radius: 6px;
            font-size: 0.9em;
            color: #a0d0ff;
            border: 1px solid #2a5a7a;
        }
        .button-group {
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
        }
        button {
            padding: 12px 24px;
            font-size: 1em;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-weight: 600;
            transition: all 0.3s;
        }
        .btn-primary {
            background: #667eea;
            color: white;
        }
        .btn-primary:hover { background: #5568d3; }
        .btn-success {
            background: #28a745;
            color: white;
        }
        .btn-success:hover { background: #218838; }
        .btn-secondary {
            background: #6c757d;
            color: white;
        }
        .btn-secondary:hover { background: #5a6268; }
        button:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
        .info-bar {
            padding: 15px 30px;
            background: #2a2a3a;
            border-bottom: 2px solid #4a4a5a;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 10px;
            color: #e0e0e0;
        }
        .info-item {
            display: flex;
            align-items: center;
            gap: 8px;
            color: #e0e0e0;
        }
        .info-item code {
            background: rgba(102, 126, 234, 0.2);
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 0.9em;
            color: #a0b0ff;
            border: 1px solid rgba(102, 126, 234, 0.3);
        }
        .main-content {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 0;
        }
        .pipeline-section {
            padding: 30px;
            border-right: 2px solid #3a3a4a;
            background: #252538;
        }
        .pipeline-section:last-child {
            border-right: none;
        }
        .section-title {
            font-size: 1.5em;
            margin-bottom: 20px;
            color: #e0e0e0;
            border-bottom: 2px solid #667eea;
            padding-bottom: 10px;
        }
        .steps-container {
            margin-bottom: 30px;
        }
        .step {
            padding: 15px;
            margin-bottom: 10px;
            border-radius: 8px;
            border-left: 4px solid #4a4a5a;
            background: #2a2a3a;
            transition: all 0.3s;
        }
        .step.pending { border-left-color: #6c757d; background: #2a2a3a; }
        .step.running { border-left-color: #007bff; background: #1a2a4a; }
        .step.waiting { border-left-color: #ffc107; background: #3a2a1a; }
        .step.complete { border-left-color: #28a745; background: #1a3a2a; }
        .step.error { border-left-color: #dc3545; background: #3a1a1a; }
        .step-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 5px;
        }
        .step-name {
            font-weight: 600;
            color: #e0e0e0;
        }
        .step-status {
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 0.85em;
            font-weight: 600;
        }
        .step-status.pending { background: #6c757d; color: white; }
        .step-status.running { background: #007bff; color: white; }
        .step-status.waiting { background: #ffc107; color: #1a1a1a; }
        .step-status.complete { background: #28a745; color: white; }
        .step-status.error { background: #dc3545; color: white; }
        .step-details {
            font-size: 0.9em;
            color: #a0a0a0;
            margin-top: 5px;
        }
        .hitl-badge {
            display: inline-block;
            background: #ffc107;
            color: #1a1a1a;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 0.75em;
            font-weight: 600;
            margin-left: 8px;
        }
        .review-section {
            margin-top: 20px;
            padding: 20px;
            background: #3a2a1a;
            border-radius: 8px;
            border: 2px solid #ffc107;
        }
        .review-section h3 {
            margin-bottom: 15px;
            color: #ffc107;
        }
        .review-content {
            background: #1a1a1a;
            color: #e0e0e0;
            padding: 15px;
            border-radius: 6px;
            max-height: 300px;
            overflow-y: auto;
            margin-bottom: 15px;
            white-space: pre-wrap;
            font-family: 'Courier New', monospace;
            font-size: 0.9em;
            border: 1px solid #4a4a4a;
        }
        .doc-viewer {
            padding: 30px;
            background: #252538;
        }
        .doc-tabs {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
            border-bottom: 2px solid #4a4a5a;
        }
        .doc-tab {
            padding: 10px 20px;
            background: transparent;
            border: none;
            border-bottom: 3px solid transparent;
            cursor: pointer;
            font-weight: 600;
            color: #a0a0a0;
            transition: all 0.3s;
        }
        .doc-tab.active {
            color: #667eea;
            border-bottom-color: #667eea;
        }
        .doc-tab:hover {
            color: #667eea;
        }
        .doc-content {
            background: #1a1a1a;
            color: #e0e0e0;
            padding: 20px;
            border-radius: 8px;
            max-height: 600px;
            overflow-y: auto;
            white-space: pre-wrap;
            font-family: 'Courier New', monospace;
            font-size: 0.9em;
            line-height: 1.6;
            border: 1px solid #4a4a4a;
        }
        .log-viewer {
            background: #0a0a0a;
            color: #d4d4d4;
            padding: 15px;
            border-radius: 8px;
            max-height: 200px;
            overflow-y: auto;
            font-family: 'Courier New', monospace;
            font-size: 0.85em;
            margin-top: 20px;
            border: 1px solid #3a3a3a;
        }
        .log-viewer div {
            margin-bottom: 5px;
        }
        @media (max-width: 1200px) {
            .main-content {
                grid-template-columns: 1fr;
            }
            .pipeline-section {
                border-right: none;
                border-bottom: 2px solid #e9ecef;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎯 Sample Requirements Transformer</h1>
            <p>Select a sample requirements document and transform it to IEEE 830 format</p>
        </div>
        
        <div class="controls">
            <div class="file-selector">
                <label for="fileSelect">Select Sample Requirements File:</label>
                <select id="fileSelect">
                    <option value="">-- Select a file --</option>
                </select>
                <div id="fileInfo" class="file-info" style="display: none;"></div>
            </div>
            
            <div class="button-group">
                <button id="startBtn" class="btn-primary" onclick="startPipeline()" disabled>Start Transformation</button>
                <button id="approveBtn" class="btn-success" onclick="approveStep()" style="display: none;">Approve & Continue</button>
                <button id="resetBtn" class="btn-secondary" onclick="resetPipeline()">Reset</button>
            </div>
        </div>
        
        <div class="info-bar">
            <div class="info-item">
                <span>🖥️</span>
                <span id="envInfo">Loading...</span>
            </div>
            <div class="info-item">
                <span>🆔</span>
                <span id="runId">Run: <code>--</code></span>
            </div>
        </div>
        
        <div class="main-content">
            <div class="pipeline-section">
                <h2 class="section-title">Pipeline Progress</h2>
                <div id="stepsContainer" class="steps-container"></div>
                <div id="reviewSection" class="review-section" style="display: none;">
                    <h3>👤 Human Review Required</h3>
                    <div id="review-content" class="review-content"></div>
                    <button class="btn-success" onclick="approveStep()">Approve & Continue</button>
                </div>
                <div class="log-viewer" id="logViewer"></div>
            </div>
            
            <div class="doc-viewer">
                <h2 class="section-title">Document Viewer</h2>
                <div class="doc-tabs">
                    <button class="doc-tab active" onclick="showDoc('source')">Source</button>
                    <button class="doc-tab" onclick="showDoc('transformed')">Transformed</button>
                    <button class="doc-tab" onclick="showDoc('validation')">Validation</button>
                </div>
                <div id="docContent" class="doc-content">Select a file to view content...</div>
            </div>
        </div>
    </div>
    
    <script>
        let selectedFilename = '';
        
        // Load sample files on page load
        fetch('/api/samples')
            .then(r => r.json())
            .then(files => {
                const select = document.getElementById('fileSelect');
                files.forEach(file => {
                    const option = document.createElement('option');
                    option.value = file.filename;
                    option.textContent = `${file.title} (${file.filename})`;
                    select.appendChild(option);
                });
                
                select.addEventListener('change', function() {
                    selectedFilename = this.value;
                    const file = files.find(f => f.filename === selectedFilename);
                    if (file) {
                        document.getElementById('fileInfo').style.display = 'block';
                        document.getElementById('fileInfo').textContent = `File: ${file.filename} | Size: ${file.size} characters`;
                        document.getElementById('startBtn').disabled = false;
                        loadFileContent(file.filename);
                    } else {
                        document.getElementById('fileInfo').style.display = 'none';
                        document.getElementById('startBtn').disabled = true;
                        document.getElementById('docContent').textContent = 'Select a file to view content...';
                    }
                });
            });
        
        function loadFileContent(filename) {
            fetch(`/api/load_file?filename=${encodeURIComponent(filename)}`)
                .then(r => r.json())
                .then(data => {
                    if (data.content) {
                        document.getElementById('docContent').textContent = data.content;
                    }
                });
        }
        
        function startPipeline() {
            if (!selectedFilename) {
                alert('Please select a file first');
                return;
            }
            
            fetch('/api/start', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({filename: selectedFilename})
            })
            .then(r => r.json())
            .then(data => {
                console.log('Pipeline started:', data);
                pollState();
            });
        }
        
        function approveStep() {
            fetch('/api/approve', {method: 'POST'})
                .then(r => r.json())
                .then(data => {
                    console.log('Approved:', data);
                    pollState();
                });
        }
        
        function resetPipeline() {
            fetch('/api/reset', {method: 'POST'})
                .then(r => r.json())
                .then(data => {
                    console.log('Reset:', data);
                    pollState();
                });
        }
        
        function showDoc(type) {
            document.querySelectorAll('.doc-tab').forEach(tab => tab.classList.remove('active'));
            event.target.classList.add('active');
            
            fetch('/api/state')
                .then(r => r.json())
                .then(state => {
                    const content = document.getElementById('docContent');
                    if (type === 'source') {
                        content.textContent = state.source_doc?.content || 'No source document loaded';
                    } else if (type === 'transformed') {
                        content.textContent = state.transformed?.content || 'Transformation not yet completed';
                    } else if (type === 'validation') {
                        content.textContent = state.validation?.feedback || 'Validation not yet completed';
                    }
                });
        }
        
        let pollInterval = null;
        function pollState() {
            if (pollInterval) clearInterval(pollInterval);
            
            pollInterval = setInterval(() => {
                fetch('/api/state')
                    .then(r => r.json())
                    .then(updateUI);
            }, 1000);
        }
        
        function updateUI(state) {
            // Update environment info
            const osIcon = state.environment.is_windows ? '🪟' : state.environment.is_macos ? '🍎' : '🐧';
            document.getElementById('envInfo').innerHTML = `${osIcon} ${state.environment.summary}`;
            document.getElementById('runId').innerHTML = `Run: <code>${state.run_id}</code>`;
            if (state.output_file) {
                const filePath = state.output_path || `_outputs/${state.output_file}`;
                document.getElementById('runId').innerHTML += `<br><span style="font-size: 0.85em; color: #a0d0ff;">📄 ${state.output_file}</span>`;
                document.getElementById('runId').innerHTML += `<br><span style="font-size: 0.75em; color: #888; font-family: monospace;">${filePath}</span>`;
            }
            
            // Update steps
            const container = document.getElementById('stepsContainer');
            container.innerHTML = state.steps.map(step => `
                <div class="step ${step.status}">
                    <div class="step-header">
                        <span class="step-name">${step.name}${step.hitl ? '<span class="hitl-badge">HITL</span>' : ''}</span>
                        <span class="step-status ${step.status}">${step.status}</span>
                    </div>
                    ${step.details ? `<div class="step-details">${step.details}</div>` : ''}
                </div>
            `).join('');
            
            // Update logs
            document.getElementById('logViewer').innerHTML = state.logs.map(log => `<div>${log}</div>`).join('');
            document.getElementById('logViewer').scrollTop = document.getElementById('logViewer').scrollHeight;
            
            // Show review section if waiting
            const reviewSection = document.getElementById('reviewSection');
            const approveBtn = document.getElementById('approveBtn');
            if (state.status === 'waiting_review') {
                reviewSection.style.display = 'block';
                approveBtn.style.display = 'inline-block';
                document.getElementById('review-content').textContent = state.mapping_explanation || 'Review the mapping analysis above';
            } else if (state.status === 'waiting_approval') {
                reviewSection.style.display = 'block';
                approveBtn.style.display = 'inline-block';
                document.getElementById('review-content').textContent = state.validation?.feedback || 'Review the validation results above';
            } else {
                reviewSection.style.display = 'none';
                approveBtn.style.display = 'none';
            }
            
            // Update document content if transformed
            if (state.transformed?.content && document.querySelector('.doc-tab.active').textContent === 'Transformed') {
                document.getElementById('docContent').textContent = state.transformed.content;
            }
            
            // Stop polling if complete or error
            if (state.status === 'complete' || state.status === 'error' || state.status === 'idle') {
                if (pollInterval) {
                    clearInterval(pollInterval);
                    pollInterval = null;
                }
            }
        }
        
        // Initial poll
        pollState();
    </script>
</body>
</html>
"""

# ============================================================
# Flask Routes
# ============================================================

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/samples')
def get_samples():
    """Get list of available sample files."""
    files = get_sample_files()
    return jsonify(files)

@app.route('/api/load_file')
def load_file():
    """Load content of a sample file."""
    filename = request.args.get('filename')
    if not filename:
        return jsonify({"error": "No filename provided"}), 400
    
    content = load_sample_file(filename)
    if content is None:
        return jsonify({"error": "File not found"}), 404
    
    return jsonify({"filename": filename, "content": content})

@app.route('/api/state')
def get_state():
    """Get current pipeline state."""
    output_file = pipeline_state.get("output_file", "")
    output_path = None
    if output_file:
        output_path = os.path.join("_outputs", output_file)
        if not os.path.exists(output_path):
            output_path = None
    
    return jsonify({
        "status": pipeline_state["status"],
        "run_id": pipeline_state.get("run_id", ""),
        "environment": pipeline_state.get("environment", {}),
        "output_file": output_file,
        "output_path": os.path.abspath(output_path) if output_path else None,
        "steps": pipeline_state["steps"],
        "logs": pipeline_state["logs"][-20:],
        "mapping_explanation": pipeline_state.get("mapping_explanation", ""),
        "validation": pipeline_state.get("validation", {}),
        "transformed": pipeline_state.get("transformed", {}),
        "source_doc": pipeline_state.get("source_doc", {})
    })

@app.route('/api/start', methods=['POST'])
def start_pipeline():
    """Start the transformation pipeline."""
    global pipeline_state
    
    data = request.json
    filename = data.get('filename')
    
    if not filename:
        return jsonify({"error": "No filename provided"}), 400
    
    # Reset state with new run_id
    pipeline_state = create_initial_state()
    pipeline_state["selected_file"] = filename
    pipeline_state["status"] = "running"
    pipeline_state["started_at"] = datetime.now().isoformat()
    
    add_log(f"Pipeline started - Run ID: {pipeline_state['run_id']}")
    add_log(f"Selected file: {filename}")
    add_log(f"Environment: {pipeline_state['environment'].get('summary', 'Unknown')}")
    
    # Run in background
    thread = threading.Thread(target=run_pipeline_async)
    thread.start()
    
    return jsonify({"status": "started", "run_id": pipeline_state["run_id"]})

@app.route('/api/approve', methods=['POST'])
def approve():
    """Approve current HITL checkpoint."""
    if pipeline_state["status"] == "waiting_review":
        thread = threading.Thread(target=continue_after_review)
        thread.start()
    elif pipeline_state["status"] == "waiting_approval":
        thread = threading.Thread(target=continue_after_approval)
        thread.start()
    
    return jsonify({"status": "approved"})

@app.route('/api/reset', methods=['POST'])
def reset():
    """Reset the pipeline state."""
    global pipeline_state
    pipeline_state = create_initial_state()
    return jsonify({"status": "reset", "run_id": pipeline_state["run_id"]})

# ============================================================
# Main
# ============================================================

if __name__ == '__main__':
    print("=" * 60)
    print("Sample Requirements Transformer - Flask Web App")
    print("=" * 60)
    print(f"Environment: {SYSTEM_ENV['summary']}")
    print(f"Ollama URL: {OLLAMA_BASE_URL}")
    print(f"Model: {OLLAMA_MODEL}")
    print(f"Sample files found: {len(get_sample_files())}")
    print("=" * 60)
    print("\nStarting server on http://localhost:5002")
    print("Press Ctrl+C to stop\n")
    
    app.run(debug=True, host='127.0.0.1', port=5002)

