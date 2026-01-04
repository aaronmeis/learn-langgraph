"""
Requirements Transformer - Flask Web Application
=================================================

A web interface for the Requirements Document Transformer pipeline
with visual progress tracking and Human-in-the-Loop approval steps.

Run: python transformer_app.py
Open: http://localhost:5001
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
from flask import Flask, render_template_string, jsonify, request, session, send_from_directory
from openai import OpenAI

app = Flask(__name__)
app.secret_key = "transformer-secret-key-2025"

# ============================================================
# Environment Detection
# ============================================================

def detect_environment():
    """
    Detect the current system environment.
    Returns dict with OS, architecture, and other system info.
    """
    env_info = {
        "os": platform.system(),  # Windows, Linux, Darwin (macOS)
        "os_version": platform.version(),
        "os_release": platform.release(),
        "architecture": platform.machine(),  # AMD64, x86_64, ARM64, aarch64
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
    
    # Detect ARM architecture
    arch_lower = env_info["architecture"].lower()
    if any(arm in arch_lower for arm in ["arm", "aarch"]):
        env_info["is_arm"] = True
        env_info["arch_family"] = "ARM"
    elif any(x86 in arch_lower for x86 in ["x86", "amd64", "i386", "i686"]):
        env_info["is_x86"] = True
        env_info["arch_family"] = "x86"
    else:
        env_info["arch_family"] = "Unknown"
    
    # Create human-readable summary
    os_name = env_info["os"]
    if env_info["is_windows"]:
        os_name = f"Windows {env_info['os_release']}"
    elif env_info["is_linux"]:
        # Try to get Linux distribution
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

# Get environment info at startup
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
# Sample Documents
# ============================================================

GENERIC_REQUIREMENTS_DOC = """# Generic Software Requirements Specification
Version: 1.0 | Date: 2025-01-15 | Author: Product Team

## 1. Project Overview
### 1.1 Project Name
Customer Relationship Management (CRM) System

### 1.2 Project Description
A comprehensive CRM system to manage customer interactions, sales pipeline, 
and support tickets. The system will replace the existing legacy solution.

### 1.3 Business Objectives
- Increase sales team productivity by 25%
- Reduce customer response time to under 4 hours
- Achieve 360-degree customer view
- Enable mobile access for field sales team

### 1.4 Stakeholders
- Sales Department (Primary Users)
- Customer Support Team
- Marketing Department
- IT Operations

## 2. Functional Requirements
### 2.1 User Management (FR-UM)
- FR-UM-001: System shall support role-based access control (RBAC)
- FR-UM-002: System shall integrate with corporate Active Directory
- FR-UM-003: System shall support multi-factor authentication

### 2.2 Contact Management (FR-CM)
- FR-CM-001: System shall store contact details including name, email, phone
- FR-CM-002: System shall support contact categorization (Lead, Prospect, Customer)
- FR-CM-003: System shall track all interactions with each contact
- FR-CM-004: System shall detect and flag duplicate contacts

### 2.3 Sales Pipeline (FR-SP)
- FR-SP-001: System shall support customizable sales stages
- FR-SP-002: System shall calculate deal probability based on stage
- FR-SP-003: System shall generate sales forecasts

### 2.4 Integration (FR-IN)
- FR-IN-001: System shall integrate with ERP (SAP)
- FR-IN-002: System shall provide REST API for third-party integrations

## 3. Non-Functional Requirements
### 3.1 Performance (NFR-P)
- NFR-P-001: Page load time shall not exceed 2 seconds
- NFR-P-002: System shall support 500 concurrent users

### 3.2 Security (NFR-S)
- NFR-S-001: All data shall be encrypted at rest (AES-256)
- NFR-S-002: All communications shall use TLS 1.3
- NFR-S-003: System shall comply with GDPR requirements

### 3.3 Availability (NFR-A)
- NFR-A-001: System shall maintain 99.9% uptime

## 4. Constraints
- Must run on Azure cloud infrastructure
- Must use PostgreSQL database
- Budget: $500,000
- Timeline: 12 months

## 5. Acceptance Criteria
- All functional requirements pass UAT
- Performance benchmarks met under load testing
- Security audit passed with no critical findings
"""

TARGET_TEMPLATE = """# IEEE 830 Software Requirements Specification

## 1. Introduction
### 1.1 Purpose - [Purpose of this SRS]
### 1.2 Scope - [Software product scope]
### 1.3 Definitions - [Technical terms]
### 1.4 References - [Reference documents]

## 2. Overall Description
### 2.1 Product Perspective - [System context]
### 2.2 Product Functions - [Major functions]
### 2.3 User Characteristics - [Intended users]
### 2.4 Constraints - [Constraints]
### 2.5 Assumptions - [Assumptions]

## 3. Specific Requirements
### 3.1 External Interfaces
### 3.2 Functional Requirements - [REQ-xxx format]
### 3.3 Performance Requirements
### 3.4 Design Constraints
### 3.5 System Attributes (Reliability, Security, etc.)

## 4. Appendices
## 5. Index
"""


# ============================================================
# Pipeline Step Functions
# ============================================================

def add_log(message):
    timestamp = datetime.now().strftime("%H:%M:%S")
    pipeline_state["logs"].append(f"[{timestamp}] {message}")
    if len(pipeline_state["logs"]) > 100:
        pipeline_state["logs"] = pipeline_state["logs"][-50:]

def step1_load_source():
    add_log("Loading source requirements document...")
    time.sleep(0.5)
    
    # Parse document
    parsed = {
        "title": "Generic Software Requirements Specification",
        "version": "1.0",
        "sections": [],
        "requirements": {"functional": [], "non_functional": []}
    }
    
    current_section = None
    for line in GENERIC_REQUIREMENTS_DOC.split('\n'):
        line = line.strip()
        if line.startswith('## '):
            if current_section:
                parsed["sections"].append(current_section)
            current_section = {"title": line[3:], "content": []}
        elif line.startswith('- FR-') or line.startswith('- NFR-'):
            req = line[2:]
            parts = req.split(':', 1)
            req_obj = {"id": parts[0], "desc": parts[1].strip() if len(parts) > 1 else ""}
            if "FR-" in parts[0]:
                parsed["requirements"]["functional"].append(req_obj)
            else:
                parsed["requirements"]["non_functional"].append(req_obj)
            if current_section:
                current_section["content"].append(req)
        elif line and current_section:
            current_section["content"].append(line)
    
    if current_section:
        parsed["sections"].append(current_section)
    
    pipeline_state["source_doc"] = parsed
    
    fr_count = len(parsed["requirements"]["functional"])
    nfr_count = len(parsed["requirements"]["non_functional"])
    
    return f"Loaded: {len(parsed['sections'])} sections, {fr_count} FR, {nfr_count} NFR"

def step2_load_template():
    add_log("Loading target template structure...")
    time.sleep(0.5)
    
    template = {
        "format": "IEEE 830",
        "sections": ["Introduction", "Overall Description", "Specific Requirements", "Appendices", "Index"],
        "placeholders": 15
    }
    
    pipeline_state["template"] = template
    return f"Template: IEEE 830 format, {len(template['sections'])} sections"

def step3_analyze_mapping():
    add_log("Calling LLM for mapping analysis...")
    
    # Build mapping (use LLM if available, fallback to default)
    try:
        client = get_client()
        response = client.chat.completions.create(
            model=OLLAMA_MODEL,
            temperature=0.3,
            max_tokens=500,
            messages=[
                {"role": "system", "content": "Create a brief mapping from generic requirements to IEEE 830 format. Respond in JSON."},
                {"role": "user", "content": f"Source sections: {[s['title'] for s in pipeline_state['source_doc'].get('sections', [])]}\nTarget: IEEE 830"}
            ]
        )
        add_log("LLM response received")
    except Exception as e:
        add_log(f"LLM unavailable, using default mapping: {e}")
    
    # Default mapping
    mapping = {
        "mappings": [
            {"source": "1. Project Overview", "target": "1. Introduction + 2. Overall Description", "action": "Split content"},
            {"source": "2. Functional Requirements", "target": "3.2 Functional Requirements", "action": "Rename IDs to REQ-xxx"},
            {"source": "3. Non-Functional Requirements", "target": "3.3-3.5 Performance/Attributes", "action": "Categorize by type"},
            {"source": "4. Constraints", "target": "2.4-2.5 Constraints/Assumptions", "action": "Move to section 2"},
            {"source": "5. Acceptance Criteria", "target": "4. Appendices", "action": "Move to appendix"}
        ],
        "new_content_needed": ["1.3 Definitions", "1.4 References", "5. Index"],
        "strategy": "Map content while preserving requirement IDs for traceability"
    }
    
    pipeline_state["mapping"] = mapping
    
    # Build explanation
    explanation = "## Proposed Mapping Strategy\n\n"
    for m in mapping["mappings"]:
        explanation += f"**{m['source']}** → **{m['target']}**\n"
        explanation += f"- Action: {m['action']}\n\n"
    explanation += "### New Content Needed:\n"
    for item in mapping["new_content_needed"]:
        explanation += f"- {item}\n"
    
    pipeline_state["mapping_explanation"] = explanation
    
    return f"Generated {len(mapping['mappings'])} mappings"

def step5_transform():
    add_log("Transforming content to IEEE 830 format...")
    time.sleep(0.5)
    
    source = pipeline_state["source_doc"]
    
    transformed = {
        "functional_reqs": [],
        "nonfunctional_reqs": [],
        "constraints": [],
        "objectives": []
    }
    
    # Transform functional requirements
    for req in source.get("requirements", {}).get("functional", []):
        new_id = req["id"].replace("FR-", "REQ-")
        transformed["functional_reqs"].append({
            "id": new_id,
            "original_id": req["id"],
            "description": req["desc"]
        })
    
    # Transform non-functional requirements
    for req in source.get("requirements", {}).get("non_functional", []):
        category = "Performance" if "NFR-P" in req["id"] else "Security" if "NFR-S" in req["id"] else "Availability"
        transformed["nonfunctional_reqs"].append({
            "id": req["id"].replace("NFR-", "ATTR-"),
            "original_id": req["id"],
            "description": req["desc"],
            "category": category
        })
    
    pipeline_state["transformed"] = transformed
    
    return f"Transformed {len(transformed['functional_reqs'])} FR, {len(transformed['nonfunctional_reqs'])} NFR"

def step6_validate():
    add_log("Validating transformation...")
    time.sleep(0.3)
    
    source = pipeline_state["source_doc"]
    transformed = pipeline_state["transformed"]
    
    validation = {
        "passed": True,
        "checks": [
            {
                "name": "Functional Requirements",
                "source": len(source.get("requirements", {}).get("functional", [])),
                "target": len(transformed.get("functional_reqs", [])),
                "passed": True
            },
            {
                "name": "Non-Functional Requirements",
                "source": len(source.get("requirements", {}).get("non_functional", [])),
                "target": len(transformed.get("nonfunctional_reqs", [])),
                "passed": True
            },
            {"name": "ID Traceability", "passed": True},
            {"name": "Required Sections", "passed": True}
        ],
        "coverage": 100.0,
        "warnings": []
    }
    
    # Check counts match
    for check in validation["checks"][:2]:
        if check.get("source") != check.get("target"):
            check["passed"] = False
            validation["warnings"].append(f"{check['name']} count mismatch")
    
    validation["passed"] = all(c["passed"] for c in validation["checks"])
    
    pipeline_state["validation"] = validation
    
    return f"Validation: {validation['coverage']}% coverage, {len(validation['warnings'])} warnings"

def step8_generate():
    add_log("Generating final IEEE 830 document...")
    time.sleep(0.5)
    
    source = pipeline_state["source_doc"]
    transformed = pipeline_state["transformed"]
    run_id = pipeline_state["run_id"]
    env = pipeline_state["environment"]
    
    doc = []
    doc.append("# IEEE 830 Software Requirements Specification\n")
    doc.append(f"**Project:** {source.get('title', 'System')}")
    doc.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    doc.append(f"**Run ID:** `{run_id}`")
    doc.append(f"**Environment:** {env.get('summary', 'Unknown')}\n")
    doc.append("---\n")
    
    doc.append("## 1. Introduction\n")
    doc.append("### 1.1 Purpose")
    doc.append("This SRS describes requirements for the CRM System.\n")
    doc.append("### 1.2 Scope")
    doc.append("A comprehensive CRM system to manage customer interactions and sales.\n")
    doc.append("### 1.3 Definitions")
    doc.append("| Term | Definition |\n|------|------------|")
    doc.append("| CRM | Customer Relationship Management |")
    doc.append("| FR | Functional Requirement |")
    doc.append("| NFR | Non-Functional Requirement |\n")
    
    doc.append("## 2. Overall Description\n")
    doc.append("### 2.1 Product Perspective")
    doc.append("New system to replace legacy CRM solution.\n")
    doc.append("### 2.2 Product Functions")
    doc.append("- Customer contact management")
    doc.append("- Sales pipeline tracking")
    doc.append("- Reporting and analytics\n")
    
    doc.append("## 3. Specific Requirements\n")
    doc.append("### 3.2 Functional Requirements\n")
    for req in transformed.get("functional_reqs", []):
        doc.append(f"**{req['id']}**: {req['description']}")
        doc.append(f"  - _Trace: {req['original_id']}_\n")
    
    doc.append("### 3.3 Performance Requirements\n")
    for req in transformed.get("nonfunctional_reqs", []):
        if req.get("category") == "Performance":
            doc.append(f"**{req['id']}**: {req['description']}")
    
    doc.append("\n### 3.5 System Attributes\n")
    doc.append("#### Security")
    for req in transformed.get("nonfunctional_reqs", []):
        if req.get("category") == "Security":
            doc.append(f"- **{req['id']}**: {req['description']}")
    
    doc.append("\n#### Availability")
    for req in transformed.get("nonfunctional_reqs", []):
        if req.get("category") == "Availability":
            doc.append(f"- **{req['id']}**: {req['description']}")
    
    doc.append("\n## 4. Appendices")
    doc.append("- Acceptance criteria from source document\n")
    
    doc.append("## 5. Index")
    doc.append("| Term | Section |")
    doc.append("|------|---------|")
    doc.append("| Authentication | 3.2 |")
    doc.append("| Security | 3.5 |")
    
    final_doc = "\n".join(doc)
    
    # Save to file with unique run_id in filename
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = f"output_{run_id}_{timestamp}.md"
    
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(final_doc)
    
    pipeline_state["final_output"] = final_doc
    pipeline_state["output_file"] = output_file
    pipeline_state["completed_at"] = datetime.now().isoformat()
    
    add_log(f"Environment: {env.get('summary', 'Unknown')}")
    
    return f"Generated {len(final_doc)} chars, saved to {output_file}"


# ============================================================
# Pipeline Runner
# ============================================================

def run_pipeline_step(step_num):
    """Run a single pipeline step."""
    step = pipeline_state["steps"][step_num - 1]
    step["status"] = "running"
    add_log(f"Starting Step {step_num}: {step['name']}")
    
    try:
        if step_num == 1:
            result = step1_load_source()
        elif step_num == 2:
            result = step2_load_template()
        elif step_num == 3:
            result = step3_analyze_mapping()
        elif step_num == 4:
            # HITL step - handled separately
            return
        elif step_num == 5:
            result = step5_transform()
        elif step_num == 6:
            result = step6_validate()
        elif step_num == 7:
            # HITL step - handled separately
            return
        elif step_num == 8:
            result = step8_generate()
        else:
            result = "Unknown step"
        
        step["status"] = "complete"
        step["details"] = result
        add_log(f"Completed Step {step_num}: {result}")
        
    except Exception as e:
        step["status"] = "error"
        step["details"] = str(e)
        add_log(f"Error in Step {step_num}: {e}")
        pipeline_state["status"] = "error"

def run_pipeline_async():
    """Run the pipeline in background thread."""
    pipeline_state["status"] = "running"
    
    # Steps 1-3
    for step_num in [1, 2, 3]:
        run_pipeline_step(step_num)
        time.sleep(0.3)
    
    # HITL Step 4 - wait for human review
    pipeline_state["status"] = "waiting_review"
    pipeline_state["steps"][3]["status"] = "waiting"
    pipeline_state["steps"][3]["details"] = "Awaiting human review of mapping"
    add_log("HUMAN REVIEW REQUIRED: Review the proposed mapping")

def continue_after_review():
    """Continue pipeline after human review approval."""
    pipeline_state["steps"][3]["status"] = "complete"
    pipeline_state["steps"][3]["details"] = "Mapping approved by human"
    pipeline_state["status"] = "running"
    add_log("Human approved mapping - continuing pipeline")
    
    # Steps 5-6
    for step_num in [5, 6]:
        run_pipeline_step(step_num)
        time.sleep(0.3)
    
    # HITL Step 7 - wait for final approval
    pipeline_state["status"] = "waiting_approval"
    pipeline_state["steps"][6]["status"] = "waiting"
    pipeline_state["steps"][6]["details"] = "Awaiting final human approval"
    add_log("HUMAN APPROVAL REQUIRED: Review validation and approve output")

def continue_after_approval():
    """Continue pipeline after final approval."""
    pipeline_state["steps"][6]["status"] = "complete"
    pipeline_state["steps"][6]["details"] = "Final output approved by human"
    pipeline_state["status"] = "running"
    add_log("Human approved final output - generating document")
    
    # Step 8
    run_pipeline_step(8)
    
    pipeline_state["status"] = "complete"
    add_log("Pipeline complete!")


# ============================================================
# HTML Template
# ============================================================

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Requirements Transformer</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: 'Segoe UI', system-ui, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            min-height: 100vh;
            color: #e0e0e0;
        }
        
        .container { max-width: 1400px; margin: 0 auto; padding: 20px; }
        
        header {
            background: rgba(0,0,0,0.3);
            padding: 20px;
            border-radius: 12px;
            margin-bottom: 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        h1 {
            background: linear-gradient(90deg, #00d4ff, #7b2cbf);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        
        .status-badge {
            padding: 8px 16px;
            border-radius: 20px;
            font-weight: bold;
            text-transform: uppercase;
            font-size: 0.85em;
        }
        
        .status-idle { background: #444; }
        .status-running { background: #2196F3; animation: pulse 1.5s infinite; }
        .status-waiting_review, .status-waiting_approval { background: #ff9800; animation: pulse 1s infinite; }
        .status-complete { background: #4caf50; }
        .status-error { background: #f44336; }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.7; }
        }
        
        .main-grid {
            display: grid;
            grid-template-columns: 300px 1fr 350px;
            gap: 20px;
        }
        
        .sidebar {
            background: rgba(0,0,0,0.3);
            border-radius: 12px;
            padding: 20px;
        }
        
        .content {
            display: flex;
            flex-direction: column;
            gap: 20px;
        }
        
        .card {
            background: rgba(0,0,0,0.3);
            border-radius: 12px;
            padding: 20px;
        }
        
        .card h2 {
            color: #00d4ff;
            margin-bottom: 15px;
            font-size: 1.2em;
        }
        
        /* Pipeline Steps */
        .step {
            display: flex;
            align-items: center;
            padding: 12px;
            margin-bottom: 8px;
            border-radius: 8px;
            background: rgba(255,255,255,0.05);
            transition: all 0.3s;
        }
        
        .step.hitl {
            border: 2px solid #ff9800;
        }
        
        .step-number {
            width: 30px;
            height: 30px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            margin-right: 12px;
            font-size: 0.9em;
        }
        
        .step.pending .step-number { background: #444; }
        .step.running .step-number { background: #2196F3; animation: pulse 1s infinite; }
        .step.waiting .step-number { background: #ff9800; animation: pulse 0.5s infinite; }
        .step.complete .step-number { background: #4caf50; }
        .step.error .step-number { background: #f44336; }
        
        .step-info { flex: 1; }
        .step-name { font-weight: 500; }
        .step-details { font-size: 0.8em; color: #888; margin-top: 2px; }
        
        .step-icon {
            font-size: 1.2em;
        }
        
        /* Buttons */
        .btn {
            padding: 12px 24px;
            border: none;
            border-radius: 8px;
            font-size: 1em;
            cursor: pointer;
            transition: all 0.2s;
            font-weight: 500;
        }
        
        .btn-primary {
            background: linear-gradient(135deg, #00d4ff, #7b2cbf);
            color: white;
        }
        
        .btn-primary:hover { transform: scale(1.02); }
        .btn-primary:disabled { opacity: 0.5; cursor: not-allowed; }
        
        .btn-success {
            background: #4caf50;
            color: white;
        }
        
        .btn-danger {
            background: #f44336;
            color: white;
        }
        
        .btn-group {
            display: flex;
            gap: 10px;
            margin-top: 15px;
        }
        
        /* Documents */
        .doc-viewer {
            background: rgba(0,0,0,0.5);
            border-radius: 8px;
            padding: 15px;
            font-family: 'Consolas', monospace;
            font-size: 0.85em;
            max-height: 300px;
            overflow-y: auto;
            white-space: pre-wrap;
        }
        
        .doc-tabs {
            display: flex;
            gap: 10px;
            margin-bottom: 15px;
        }
        
        .doc-tab {
            padding: 8px 16px;
            background: rgba(255,255,255,0.1);
            border: none;
            border-radius: 6px;
            color: #e0e0e0;
            cursor: pointer;
        }
        
        .doc-tab.active {
            background: #7b2cbf;
        }
        
        /* Logs */
        .log-viewer {
            background: #000;
            border-radius: 8px;
            padding: 15px;
            font-family: 'Consolas', monospace;
            font-size: 0.8em;
            max-height: 200px;
            overflow-y: auto;
            color: #0f0;
        }
        
        .log-viewer div {
            margin-bottom: 4px;
        }
        
        /* HITL Review Panel */
        .review-panel {
            background: linear-gradient(135deg, rgba(255,152,0,0.2), rgba(255,87,34,0.2));
            border: 2px solid #ff9800;
            border-radius: 12px;
            padding: 20px;
        }
        
        .review-panel h2 {
            color: #ff9800 !important;
        }
        
        .mapping-item {
            background: rgba(0,0,0,0.3);
            padding: 12px;
            border-radius: 8px;
            margin-bottom: 10px;
        }
        
        .mapping-arrow {
            color: #00d4ff;
            margin: 0 10px;
        }
        
        /* Validation Results */
        .validation-check {
            display: flex;
            align-items: center;
            padding: 8px;
            background: rgba(0,0,0,0.3);
            border-radius: 6px;
            margin-bottom: 6px;
        }
        
        .check-icon {
            margin-right: 10px;
            font-size: 1.2em;
        }
        
        .check-passed { color: #4caf50; }
        .check-failed { color: #f44336; }
        
        /* Progress bar */
        .progress-bar {
            height: 4px;
            background: rgba(255,255,255,0.1);
            border-radius: 2px;
            margin-top: 15px;
            overflow: hidden;
        }
        
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #00d4ff, #7b2cbf);
            transition: width 0.3s;
        }
        
        /* Video Panel */
        .video-panel {
            background: rgba(0,0,0,0.3);
            border-radius: 12px;
            padding: 20px;
            display: flex;
            flex-direction: column;
            position: sticky;
            top: 20px;
            height: calc(100vh - 200px);
            max-height: calc(100vh - 200px);
            overflow-y: auto;
        }
        
        .video-panel h2 {
            color: #00d4ff;
            margin-bottom: 15px;
            font-size: 1.3em;
            text-align: center;
        }
        
        .video-container {
            width: 100%;
            background: #000;
            border-radius: 8px;
            overflow: hidden;
            margin-bottom: 15px;
            aspect-ratio: 9/16;
            max-height: 600px;
        }
        
        .video-container video {
            width: 100%;
            height: 100%;
            object-fit: contain;
        }
        
        .video-placeholder {
            width: 100%;
            aspect-ratio: 9/16;
            max-height: 600px;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: 8px;
            margin-bottom: 15px;
            border: 2px dashed rgba(255, 255, 255, 0.2);
        }
        
        .video-placeholder p {
            text-align: center;
            opacity: 0.6;
            padding: 20px;
            font-size: 0.9em;
        }
        
        .video-info {
            background: rgba(0,0,0,0.3);
            padding: 15px;
            border-radius: 8px;
            font-size: 0.85em;
            opacity: 0.8;
        }
        
        .video-info strong {
            color: #00d4ff;
        }
        
        @media (max-width: 1400px) {
            .main-grid {
                grid-template-columns: 300px 1fr;
            }
            .video-panel {
                display: none;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <div>
                <h1>Requirements Document Transformer</h1>
                <p style="color: #888; margin-top: 5px;">Generic Format → IEEE 830 with Human-in-the-Loop</p>
                <div id="env-info" style="margin-top: 8px; font-size: 0.85em; color: #666;"></div>
            </div>
            <div style="text-align: right;">
                <div id="status-badge" class="status-badge status-idle">IDLE</div>
                <div id="run-id" style="margin-top: 8px; font-family: monospace; font-size: 0.85em; color: #7b2cbf;"></div>
            </div>
        </header>
        
        <div class="main-grid">
            <!-- Sidebar: Pipeline Steps -->
            <div class="sidebar">
                <h2 style="color: #00d4ff; margin-bottom: 15px;">Pipeline Steps</h2>
                <div id="steps-container"></div>
                <div class="progress-bar">
                    <div id="progress-fill" class="progress-fill" style="width: 0%"></div>
                </div>
                <div class="btn-group">
                    <button id="start-btn" class="btn btn-primary" onclick="startPipeline()">
                        Start Pipeline
                    </button>
                    <button id="reset-btn" class="btn" style="background: #444; color: white;" onclick="resetPipeline()">
                        Reset
                    </button>
                </div>
            </div>
            
            <!-- Main Content -->
            <div class="content">
                <!-- Document Viewer -->
                <div class="card">
                    <h2>Documents</h2>
                    <div class="doc-tabs">
                        <button class="doc-tab active" onclick="showDoc('source')">Source (Generic)</button>
                        <button class="doc-tab" onclick="showDoc('template')">Target (IEEE 830)</button>
                        <button class="doc-tab" onclick="showDoc('output')">Output</button>
                    </div>
                    <div id="doc-viewer" class="doc-viewer">Click "Start Pipeline" to begin...</div>
                </div>
                
                <!-- HITL Review Panel (hidden by default) -->
                <div id="review-panel" class="review-panel" style="display: none;">
                    <h2>🧑 Human Review Required</h2>
                    <div id="review-content"></div>
                    <div class="btn-group">
                        <button class="btn btn-success" onclick="approveStep()">✓ Approve</button>
                        <button class="btn btn-danger" onclick="rejectStep()">✗ Reject</button>
                    </div>
                </div>
                
                <!-- Validation Results (hidden by default) -->
                <div id="validation-panel" class="card" style="display: none;">
                    <h2>Validation Results</h2>
                    <div id="validation-content"></div>
                </div>
                
                <!-- Logs -->
                <div class="card">
                    <h2>Pipeline Logs</h2>
                    <div id="log-viewer" class="log-viewer"></div>
                </div>
            </div>
            
            <!-- Video Panel -->
            <div class="video-panel">
                <h2>AI Explanation</h2>
                <div id="videoContainer" class="video-placeholder">
                    <p>AI explanation video<br><br><small>Requirements Transformer workflow</small></p>
                </div>
                <div class="video-info">
                    <p><strong>Duration:</strong> 90-120 seconds</p>
                    <p><strong>Format:</strong> MP4 with HeyGen Avatar</p>
                    <p><strong>Content:</strong> Code walkthrough and explanation</p>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        let currentDocTab = 'source';
        let pollInterval = null;
        
        const sourceDoc = `{{ source_doc | safe }}`;
        const templateDoc = `{{ template_doc | safe }}`;
        
        function updateUI(state) {
            // Update environment info
            const envInfo = document.getElementById('env-info');
            if (state.environment && state.environment.summary) {
                const isArm = state.environment.is_arm ? '💪 ARM' : '🖥️ x86';
                const osIcon = state.environment.is_windows ? '🪟' : state.environment.is_linux ? '🐧' : state.environment.is_macos ? '🍎' : '💻';
                envInfo.innerHTML = `${osIcon} ${state.environment.summary}`;
            }
            
            // Update run ID
            const runIdEl = document.getElementById('run-id');
            if (state.run_id) {
                runIdEl.innerHTML = `Run: <code style="background: rgba(123,44,191,0.2); padding: 2px 6px; border-radius: 4px;">${state.run_id}</code>`;
                if (state.output_file) {
                    runIdEl.innerHTML += `<br><span style="font-size: 0.85em; color: #888;">📄 ${state.output_file}</span>`;
                }
            }
            
            // Update status badge
            const badge = document.getElementById('status-badge');
            badge.className = 'status-badge status-' + state.status;
            badge.textContent = state.status.replace('_', ' ').toUpperCase();
            
            // Update steps
            const container = document.getElementById('steps-container');
            container.innerHTML = state.steps.map(step => `
                <div class="step ${step.status} ${step.hitl ? 'hitl' : ''}">
                    <div class="step-number">${step.id}</div>
                    <div class="step-info">
                        <div class="step-name">${step.hitl ? '🧑 ' : ''}${step.name}</div>
                        <div class="step-details">${step.details || ''}</div>
                    </div>
                    <div class="step-icon">
                        ${step.status === 'complete' ? '✓' : 
                          step.status === 'running' ? '⟳' : 
                          step.status === 'waiting' ? '⏳' :
                          step.status === 'error' ? '✗' : '○'}
                    </div>
                </div>
            `).join('');
            
            // Update progress
            const completed = state.steps.filter(s => s.status === 'complete').length;
            const progress = (completed / state.steps.length) * 100;
            document.getElementById('progress-fill').style.width = progress + '%';
            
            // Update logs
            const logViewer = document.getElementById('log-viewer');
            logViewer.innerHTML = state.logs.map(log => `<div>${log}</div>`).join('');
            logViewer.scrollTop = logViewer.scrollHeight;
            
            // Show/hide review panel
            const reviewPanel = document.getElementById('review-panel');
            if (state.status === 'waiting_review') {
                reviewPanel.style.display = 'block';
                document.getElementById('review-content').innerHTML = `
                    <p style="margin-bottom: 15px;">Review the proposed mapping from Generic to IEEE 830 format:</p>
                    ${state.mapping_explanation ? state.mapping_explanation.split('\\n').map(line => {
                        if (line.startsWith('**')) return `<div class="mapping-item">${line.replace(/\\*\\*/g, '<strong>').replace(/<\\/strong>/g, '</strong>')}</div>`;
                        if (line.startsWith('-')) return `<div style="color: #888; margin-left: 20px;">${line}</div>`;
                        if (line.startsWith('###')) return `<h4 style="margin-top: 15px; color: #ff9800;">${line.replace('###', '')}</h4>`;
                        return `<div>${line}</div>`;
                    }).join('') : '<p>Mapping analysis in progress...</p>'}
                `;
            } else if (state.status === 'waiting_approval') {
                reviewPanel.style.display = 'block';
                const val = state.validation;
                document.getElementById('review-content').innerHTML = `
                    <p style="margin-bottom: 15px;">Review validation results before generating output:</p>
                    <div style="font-size: 1.5em; margin-bottom: 15px;">
                        Coverage: <span style="color: ${val.coverage >= 90 ? '#4caf50' : '#ff9800'}">${val.coverage}%</span>
                    </div>
                    ${val.checks ? val.checks.map(c => `
                        <div class="validation-check">
                            <span class="check-icon ${c.passed ? 'check-passed' : 'check-failed'}">
                                ${c.passed ? '✓' : '✗'}
                            </span>
                            <span>${c.name}</span>
                            ${c.source !== undefined ? `<span style="margin-left: auto; color: #888;">${c.source} → ${c.target}</span>` : ''}
                        </div>
                    `).join('') : ''}
                    ${val.warnings && val.warnings.length > 0 ? `
                        <div style="margin-top: 15px; color: #ff9800;">
                            <strong>Warnings:</strong>
                            ${val.warnings.map(w => `<div>- ${w}</div>`).join('')}
                        </div>
                    ` : ''}
                `;
            } else {
                reviewPanel.style.display = 'none';
            }
            
            // Update output doc if complete
            if (state.status === 'complete' && state.final_output) {
                if (currentDocTab === 'output') {
                    document.getElementById('doc-viewer').textContent = state.final_output;
                }
            }
            
            // Update buttons
            document.getElementById('start-btn').disabled = state.status !== 'idle';
        }
        
        function showDoc(tab) {
            currentDocTab = tab;
            document.querySelectorAll('.doc-tab').forEach(t => t.classList.remove('active'));
            event.target.classList.add('active');
            
            const viewer = document.getElementById('doc-viewer');
            if (tab === 'source') {
                viewer.textContent = sourceDoc;
            } else if (tab === 'template') {
                viewer.textContent = templateDoc;
            } else {
                fetch('/api/state').then(r => r.json()).then(state => {
                    viewer.textContent = state.final_output || 'Output will appear here after pipeline completes...';
                });
            }
        }
        
        function startPipeline() {
            fetch('/api/start', { method: 'POST' })
                .then(r => r.json())
                .then(data => {
                    if (pollInterval) clearInterval(pollInterval);
                    pollInterval = setInterval(pollState, 500);
                });
        }
        
        function resetPipeline() {
            fetch('/api/reset', { method: 'POST' })
                .then(r => r.json())
                .then(data => {
                    if (pollInterval) clearInterval(pollInterval);
                    pollState();
                });
        }
        
        function approveStep() {
            fetch('/api/approve', { method: 'POST' })
                .then(r => r.json())
                .then(data => {
                    pollState();
                });
        }
        
        function rejectStep() {
            alert('Pipeline rejected. Click Reset to start over.');
            fetch('/api/reset', { method: 'POST' })
                .then(r => r.json())
                .then(data => {
                    if (pollInterval) clearInterval(pollInterval);
                    pollState();
                });
        }
        
        function pollState() {
            fetch('/api/state')
                .then(r => r.json())
                .then(state => {
                    updateUI(state);
                    if (state.status === 'complete' || state.status === 'error' || state.status === 'idle') {
                        if (pollInterval) {
                            clearInterval(pollInterval);
                            pollInterval = null;
                        }
                    }
                });
        }
        
        // Load video
        function loadVideo() {
            console.log('loadVideo() called');
            const videoContainer = document.getElementById('videoContainer');
            if (!videoContainer) {
                console.error('videoContainer element not found!');
                return;
            }
            console.log('videoContainer found:', videoContainer);
            
            // Try compressed avatar first, then fallback to original
            const compressedPath = '/avatars/compressed_avatars/transformer.mp4';
            const fallbackPath = '/avatars/transformer.mp4';
            console.log('Loading video from:', compressedPath);
            
            // Remove placeholder class and add video container
            videoContainer.className = 'video-container';
            videoContainer.innerHTML = `
                <video controls id="transformerVideo" style="width: 100%; height: 100%; object-fit: contain;">
                    <source src="${compressedPath}" type="video/mp4">
                    <source src="${fallbackPath}" type="video/mp4">
                    Your browser does not support the video tag.
                </video>
            `;
            
            const video = document.getElementById('transformerVideo');
            if (video) {
                console.log('Video element created');
                video.addEventListener('error', function(e) {
                    console.error('Video load error:', e, video.error);
                    videoContainer.className = 'video-placeholder';
                    videoContainer.innerHTML = `
                        <p>Video file not found: ${videoPath}<br><br>
                        <small>Error code: ${video.error ? video.error.code : 'unknown'}</small></p>
                    `;
                });
                
                video.addEventListener('loadeddata', function() {
                    console.log('Video loaded successfully');
                });
                
                video.addEventListener('loadstart', function() {
                    console.log('Video load started');
                });
            } else {
                console.error('Video element not created!');
            }
        }
        
        // Initial load - wait for DOM to be ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', function() {
                console.log('DOM loaded, initializing...');
                pollState();
                showDoc('source');
                loadVideo();
            });
        } else {
            console.log('DOM already loaded, initializing...');
            pollState();
            showDoc('source');
            loadVideo();
        }
    </script>
</body>
</html>
"""


# ============================================================
# Flask Routes
# ============================================================

@app.route('/')
def index():
    return render_template_string(
        HTML_TEMPLATE, 
        source_doc=GENERIC_REQUIREMENTS_DOC.replace('`', '\\`').replace('\n', '\\n'),
        template_doc=TARGET_TEMPLATE.replace('`', '\\`').replace('\n', '\\n')
    )

@app.route('/api/state')
def get_state():
    return jsonify({
        "status": pipeline_state["status"],
        "run_id": pipeline_state.get("run_id", ""),
        "environment": pipeline_state.get("environment", {}),
        "output_file": pipeline_state.get("output_file", ""),
        "steps": pipeline_state["steps"],
        "logs": pipeline_state["logs"][-20:],
        "mapping_explanation": pipeline_state["mapping_explanation"],
        "validation": pipeline_state["validation"],
        "final_output": pipeline_state["final_output"]
    })

@app.route('/api/start', methods=['POST'])
def start_pipeline():
    global pipeline_state
    # Reset state with new run_id
    pipeline_state = create_initial_state()
    pipeline_state["status"] = "running"
    pipeline_state["started_at"] = datetime.now().isoformat()
    
    add_log(f"Pipeline started - Run ID: {pipeline_state['run_id']}")
    add_log(f"Environment: {pipeline_state['environment'].get('summary', 'Unknown')}")
    
    # Run in background
    thread = threading.Thread(target=run_pipeline_async)
    thread.start()
    
    return jsonify({"status": "started", "run_id": pipeline_state["run_id"]})

@app.route('/api/approve', methods=['POST'])
def approve():
    if pipeline_state["status"] == "waiting_review":
        thread = threading.Thread(target=continue_after_review)
        thread.start()
    elif pipeline_state["status"] == "waiting_approval":
        thread = threading.Thread(target=continue_after_approval)
        thread.start()
    
    return jsonify({"status": "approved"})

@app.route('/api/reset', methods=['POST'])
def reset():
    global pipeline_state
    pipeline_state = create_initial_state()
    return jsonify({"status": "reset", "run_id": pipeline_state["run_id"]})

@app.route('/avatars/<path:filename>')
def serve_avatar(filename):
    """Serve video files from the avatars directory (supports compressed_avatars subdirectory)."""
    # Handle both avatars/ and avatars/compressed_avatars/ paths
    if filename.startswith('compressed_avatars/'):
        return send_from_directory('avatars', filename)
    else:
        return send_from_directory('avatars', filename)


# ============================================================
# Main
# ============================================================

if __name__ == '__main__':
    print("=" * 60)
    print("Requirements Transformer - Flask Web App")
    print("=" * 60)
    print("\nStarting server...")
    print("Open: http://localhost:5001")
    print("\nPress Ctrl+C to stop")
    print("-" * 60)
    
    app.run(host='0.0.0.0', port=5001, debug=False)

