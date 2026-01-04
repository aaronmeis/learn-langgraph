"""
LangGraph Advanced Example: Requirements Document Transformer
=============================================================

This pipeline takes a filled-out generic requirements document and transforms
it to match a different requirements template format, with human-in-the-loop
review between key steps.

Pipeline Flow:
--------------
START → step1_load_source → step2_load_template → step3_analyze_mapping 
      → [HUMAN REVIEW] → step4_transform → step5_validate 
      → [HUMAN APPROVAL] → step6_generate_output → END

Human-in-the-Loop:
------------------
- After step 3: Human reviews the proposed mapping before transformation
- After step 5: Human approves the final output before generation
"""

import warnings
# Suppress Pydantic V1 deprecation warnings for Python 3.14+
warnings.filterwarnings("ignore", category=UserWarning, module="langchain_core.*")

import json
import os
import platform
import struct
import uuid
from datetime import datetime
from typing import Literal, Optional
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, START, END
from openai import OpenAI

# ============================================================
# Platform Detection
# ============================================================

def detect_platform():
    """
    Detect the current platform environment.
    Returns dict with OS, architecture, and system info.
    """
    info = {
        "os": platform.system(),  # Windows, Linux, Darwin (macOS)
        "os_release": platform.release(),
        "os_version": platform.version(),
        "architecture": platform.machine(),  # AMD64, x86_64, ARM64, aarch64
        "processor": platform.processor(),
        "python_version": platform.python_version(),
        "bits": struct.calcsize("P") * 8,
        "is_arm": False,
        "is_windows": False,
        "is_linux": False,
        "is_macos": False
    }
    
    # Detect ARM architecture
    arch_lower = info["architecture"].lower()
    info["is_arm"] = any(arm in arch_lower for arm in ["arm", "aarch"])
    
    # Detect OS type
    os_name = info["os"].lower()
    info["is_windows"] = os_name == "windows"
    info["is_linux"] = os_name == "linux"
    info["is_macos"] = os_name == "darwin"
    
    # Build summary string
    os_str = "Windows" if info["is_windows"] else "Linux" if info["is_linux"] else "macOS" if info["is_macos"] else info["os"]
    arch_str = "ARM64" if info["is_arm"] else info["architecture"]
    info["summary"] = f"{os_str} | {arch_str} | {info['bits']}-bit | Python {info['python_version']}"
    
    return info

# Get platform info at startup
PLATFORM_INFO = detect_platform()

def generate_run_id():
    """Generate a unique run ID (short UUID)."""
    return str(uuid.uuid4())[:8]

def generate_output_filename(run_id: str, base_name: str = "transformed_ieee830") -> str:
    """Generate unique output filename with timestamp and GUID."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{base_name}_{timestamp}_{run_id}.md"

# ============================================================
# Configuration
# ============================================================

OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434/v1")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.2:1b")

def get_client():
    return OpenAI(base_url=OLLAMA_BASE_URL, api_key="ollama")

def log(msg: str):
    print(msg)


# ============================================================
# Sample Generic Requirements Document (Filled Out)
# ============================================================

GENERIC_REQUIREMENTS_DOC = """
# Generic Software Requirements Specification
Version: 1.0
Date: 2025-01-15
Author: Product Team

## 1. Project Overview
### 1.1 Project Name
Customer Relationship Management (CRM) System

### 1.2 Project Description
A comprehensive CRM system to manage customer interactions, sales pipeline, 
and support tickets. The system will replace the existing legacy solution 
and integrate with our ERP system.

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
- Executive Leadership

## 2. Functional Requirements

### 2.1 User Management (FR-UM)
- FR-UM-001: System shall support role-based access control (RBAC)
- FR-UM-002: System shall integrate with corporate Active Directory
- FR-UM-003: System shall support multi-factor authentication
- FR-UM-004: System shall maintain audit logs of all user activities

### 2.2 Contact Management (FR-CM)
- FR-CM-001: System shall store contact details including name, email, phone, address
- FR-CM-002: System shall support contact categorization (Lead, Prospect, Customer)
- FR-CM-003: System shall track all interactions with each contact
- FR-CM-004: System shall support bulk import/export of contacts (CSV, Excel)
- FR-CM-005: System shall detect and flag duplicate contacts

### 2.3 Sales Pipeline (FR-SP)
- FR-SP-001: System shall support customizable sales stages
- FR-SP-002: System shall calculate deal probability based on stage
- FR-SP-003: System shall generate sales forecasts
- FR-SP-004: System shall send alerts for stale opportunities
- FR-SP-005: System shall track win/loss reasons

### 2.4 Reporting & Analytics (FR-RA)
- FR-RA-001: System shall provide real-time dashboard
- FR-RA-002: System shall support custom report builder
- FR-RA-003: System shall export reports to PDF, Excel
- FR-RA-004: System shall schedule automated report delivery

### 2.5 Integration (FR-IN)
- FR-IN-001: System shall integrate with ERP (SAP)
- FR-IN-002: System shall integrate with email (Microsoft 365)
- FR-IN-003: System shall provide REST API for third-party integrations
- FR-IN-004: System shall sync with mobile devices

## 3. Non-Functional Requirements

### 3.1 Performance (NFR-P)
- NFR-P-001: Page load time shall not exceed 2 seconds
- NFR-P-002: System shall support 500 concurrent users
- NFR-P-003: Search results shall return within 1 second
- NFR-P-004: Report generation shall complete within 30 seconds

### 3.2 Security (NFR-S)
- NFR-S-001: All data shall be encrypted at rest (AES-256)
- NFR-S-002: All communications shall use TLS 1.3
- NFR-S-003: System shall comply with GDPR requirements
- NFR-S-004: Password policy shall require minimum 12 characters

### 3.3 Availability (NFR-A)
- NFR-A-001: System shall maintain 99.9% uptime
- NFR-A-002: Planned maintenance windows shall not exceed 4 hours/month
- NFR-A-003: System shall support disaster recovery with RPO < 1 hour

### 3.4 Scalability (NFR-SC)
- NFR-SC-001: System shall scale to 10,000 users
- NFR-SC-002: Database shall handle 10 million contact records

## 4. Constraints & Assumptions

### 4.1 Technical Constraints
- Must run on Azure cloud infrastructure
- Must use PostgreSQL database
- Must support modern browsers (Chrome, Firefox, Edge, Safari)

### 4.2 Business Constraints
- Budget: $500,000
- Timeline: 12 months
- Team: 8 developers, 2 QA, 1 BA, 1 PM

### 4.3 Assumptions
- Users have reliable internet connectivity
- Corporate AD is available for integration
- ERP API documentation is current

## 5. Acceptance Criteria
- All functional requirements pass UAT
- Performance benchmarks met under load testing
- Security audit passed with no critical findings
- User training completed for 90% of users
"""


# ============================================================
# Target Template (Different Format - IEEE 830 Style)
# ============================================================

TARGET_TEMPLATE = """
# IEEE 830 Software Requirements Specification Template

## 1. Introduction
### 1.1 Purpose
[Describe the purpose of this SRS document]

### 1.2 Scope
[Define the software product scope, benefits, objectives]

### 1.3 Definitions, Acronyms, Abbreviations
[List technical terms and their definitions]

### 1.4 References
[List reference documents]

### 1.5 Overview
[Describe rest of SRS organization]

## 2. Overall Description
### 2.1 Product Perspective
[Describe system context, interfaces, constraints]

### 2.2 Product Functions
[High-level summary of major functions]

### 2.3 User Characteristics
[Describe intended users and their expertise]

### 2.4 Constraints
[Regulatory, hardware, software, operational constraints]

### 2.5 Assumptions and Dependencies
[List assumptions and external dependencies]

## 3. Specific Requirements
### 3.1 External Interface Requirements
#### 3.1.1 User Interfaces
[UI requirements]

#### 3.1.2 Hardware Interfaces
[Hardware interface requirements]

#### 3.1.3 Software Interfaces
[Software interface requirements]

#### 3.1.4 Communication Interfaces
[Network/protocol requirements]

### 3.2 Functional Requirements
[Organized by feature or user class]
#### 3.2.1 Feature 1
[REQ-001: Requirement description]
[REQ-002: Requirement description]

### 3.3 Performance Requirements
[Quantitative performance specs]

### 3.4 Design Constraints
[Standards, hardware limitations]

### 3.5 Software System Attributes
#### 3.5.1 Reliability
[Reliability requirements]

#### 3.5.2 Availability  
[Availability requirements]

#### 3.5.3 Security
[Security requirements]

#### 3.5.4 Maintainability
[Maintainability requirements]

#### 3.5.5 Portability
[Portability requirements]

## 4. Appendices
[Supporting information]

## 5. Index
[Alphabetical index of terms]
"""


# ============================================================
# Pipeline State with Human-in-the-Loop Support
# ============================================================

class TransformState(BaseModel):
    """State for the requirements transformation pipeline."""
    
    # Run identification
    run_id: str = Field(default="", description="Unique run identifier (GUID)")
    platform_info: dict = Field(default_factory=dict, description="Platform/environment info")
    
    # Input documents
    source_document: str = Field(default="", description="Original requirements document")
    target_template: str = Field(default="", description="Target format template")
    
    # Parsed data
    source_parsed: dict = Field(default_factory=dict, description="Parsed source requirements")
    template_structure: dict = Field(default_factory=dict, description="Target template structure")
    
    # Mapping (for human review)
    proposed_mapping: dict = Field(default_factory=dict, description="Proposed source→target mapping")
    mapping_explanation: str = Field(default="", description="Explanation of mapping decisions")
    
    # Human-in-the-loop fields
    human_review_required: bool = Field(default=False, description="Waiting for human review")
    human_feedback: str = Field(default="", description="Human's feedback/modifications")
    human_approved: bool = Field(default=False, description="Human approved to proceed")
    review_stage: str = Field(default="", description="Current review stage")
    
    # Transformation results
    transformed_content: dict = Field(default_factory=dict, description="Content mapped to new template")
    validation_results: dict = Field(default_factory=dict, description="Validation check results")
    
    # Final output
    final_document: str = Field(default="", description="Final transformed document")
    output_file: str = Field(default="", description="Path to output file")
    
    # Metadata
    current_step: str = Field(default="", description="Current processing step")
    errors: list[str] = Field(default_factory=list)
    processing_log: list[str] = Field(default_factory=list)
    started_at: str = Field(default="", description="Pipeline start time")


# ============================================================
# Step 1: Load Source Requirements Document
# ============================================================

def step1_load_source(state: TransformState) -> dict:
    """Load and parse the source requirements document."""
    log("\n[Step 1] Loading source requirements document...")
    
    processing_log = state.processing_log.copy()
    processing_log.append(f"Step 1 started: {datetime.now().isoformat()}")
    
    # Use the generic requirements document
    source = GENERIC_REQUIREMENTS_DOC
    
    # Parse into structured format
    parsed = {
        "title": "",
        "version": "",
        "date": "",
        "sections": [],
        "requirements": {
            "functional": [],
            "non_functional": []
        },
        "metadata": {}
    }
    
    current_section = None
    current_subsection = None
    
    for line in source.split('\n'):
        line_stripped = line.strip()
        
        # Extract metadata
        if line_stripped.startswith('Version:'):
            parsed["version"] = line_stripped.replace('Version:', '').strip()
        elif line_stripped.startswith('Date:'):
            parsed["date"] = line_stripped.replace('Date:', '').strip()
        elif line_stripped.startswith('Author:'):
            parsed["metadata"]["author"] = line_stripped.replace('Author:', '').strip()
        
        # Main title
        elif line_stripped.startswith('# ') and not line_stripped.startswith('## '):
            parsed["title"] = line_stripped[2:].strip()
        
        # Section headers
        elif line_stripped.startswith('## '):
            if current_section:
                parsed["sections"].append(current_section)
            current_section = {
                "title": line_stripped[3:].strip(),
                "subsections": [],
                "content": []
            }
            current_subsection = None
        
        # Subsection headers
        elif line_stripped.startswith('### '):
            if current_section:
                current_subsection = {
                    "title": line_stripped[4:].strip(),
                    "items": []
                }
                current_section["subsections"].append(current_subsection)
        
        # Requirements (FR- or NFR-)
        elif line_stripped.startswith('- FR-') or line_stripped.startswith('- NFR-'):
            req_text = line_stripped[2:]  # Remove "- "
            req_parts = req_text.split(':', 1)
            req = {
                "id": req_parts[0].strip(),
                "description": req_parts[1].strip() if len(req_parts) > 1 else "",
                "category": "functional" if "FR-" in req_parts[0] else "non_functional"
            }
            
            if req["category"] == "functional":
                parsed["requirements"]["functional"].append(req)
            else:
                parsed["requirements"]["non_functional"].append(req)
            
            if current_subsection:
                current_subsection["items"].append(req)
        
        # Regular content
        elif line_stripped and current_subsection:
            if line_stripped.startswith('- '):
                current_subsection["items"].append({"text": line_stripped[2:]})
            else:
                current_subsection["items"].append({"text": line_stripped})
    
    # Don't forget the last section
    if current_section:
        parsed["sections"].append(current_section)
    
    log(f"    Loaded document: {parsed['title']}")
    log(f"    Sections: {len(parsed['sections'])}")
    log(f"    Functional requirements: {len(parsed['requirements']['functional'])}")
    log(f"    Non-functional requirements: {len(parsed['requirements']['non_functional'])}")
    
    processing_log.append(f"Loaded {len(parsed['sections'])} sections")
    
    return {
        "source_document": source,
        "source_parsed": parsed,
        "current_step": "step1_load_source",
        "processing_log": processing_log,
        "started_at": datetime.now().isoformat()
    }


# ============================================================
# Step 2: Load Target Template Structure
# ============================================================

def step2_load_template(state: TransformState) -> dict:
    """Load and analyze the target template structure."""
    log("\n[Step 2] Loading target template structure...")
    
    processing_log = state.processing_log.copy()
    processing_log.append(f"Step 2 started: {datetime.now().isoformat()}")
    
    # Parse template structure
    template_structure = {
        "format": "IEEE 830",
        "sections": [],
        "placeholders": []
    }
    
    current_section = None
    current_subsection = None
    
    for line in TARGET_TEMPLATE.split('\n'):
        line_stripped = line.strip()
        
        # Section headers
        if line_stripped.startswith('## '):
            if current_section:
                template_structure["sections"].append(current_section)
            current_section = {
                "number": "",
                "title": line_stripped[3:].strip(),
                "subsections": [],
                "placeholders": []
            }
            # Extract section number
            parts = current_section["title"].split(' ', 1)
            if parts[0].replace('.', '').isdigit():
                current_section["number"] = parts[0]
                current_section["title"] = parts[1] if len(parts) > 1 else ""
            current_subsection = None
        
        # Subsection headers
        elif line_stripped.startswith('### ') or line_stripped.startswith('#### '):
            prefix_len = 4 if line_stripped.startswith('### ') else 5
            if current_section:
                current_subsection = {
                    "title": line_stripped[prefix_len:].strip(),
                    "level": 3 if prefix_len == 4 else 4,
                    "placeholders": []
                }
                current_section["subsections"].append(current_subsection)
        
        # Placeholders [text in brackets]
        elif '[' in line_stripped and ']' in line_stripped:
            placeholder = line_stripped
            if current_subsection:
                current_subsection["placeholders"].append(placeholder)
            elif current_section:
                current_section["placeholders"].append(placeholder)
            template_structure["placeholders"].append(placeholder)
    
    # Don't forget the last section
    if current_section:
        template_structure["sections"].append(current_section)
    
    log(f"    Template format: {template_structure['format']}")
    log(f"    Template sections: {len(template_structure['sections'])}")
    log(f"    Placeholders to fill: {len(template_structure['placeholders'])}")
    
    processing_log.append(f"Template has {len(template_structure['sections'])} sections")
    
    return {
        "target_template": TARGET_TEMPLATE,
        "template_structure": template_structure,
        "current_step": "step2_load_template",
        "processing_log": processing_log
    }


# ============================================================
# Step 3: Analyze and Propose Mapping (LLM-Assisted)
# ============================================================

def step3_analyze_mapping(state: TransformState) -> dict:
    """Use LLM to analyze source and propose mapping to target template."""
    log("\n[Step 3] Analyzing and proposing mapping...")
    
    processing_log = state.processing_log.copy()
    processing_log.append(f"Step 3 started: {datetime.now().isoformat()}")
    
    client = get_client()
    
    # Build context for LLM
    source_summary = {
        "title": state.source_parsed.get("title"),
        "sections": [s["title"] for s in state.source_parsed.get("sections", [])],
        "functional_reqs": len(state.source_parsed.get("requirements", {}).get("functional", [])),
        "nonfunctional_reqs": len(state.source_parsed.get("requirements", {}).get("non_functional", []))
    }
    
    template_summary = {
        "format": state.template_structure.get("format"),
        "sections": [s["title"] for s in state.template_structure.get("sections", [])]
    }
    
    prompt = f"""You are a requirements analyst. Map source document sections to target template.

SOURCE DOCUMENT STRUCTURE:
{json.dumps(source_summary, indent=2)}

TARGET TEMPLATE (IEEE 830):
{json.dumps(template_summary, indent=2)}

Create a mapping showing which source sections map to which target sections.
Respond in JSON format:
{{
    "mapping": [
        {{"source": "source section", "target": "target section", "notes": "explanation"}}
    ],
    "unmapped_source": ["sections with no target"],
    "target_needs_content": ["target sections needing new content"],
    "transformation_notes": "overall strategy"
}}"""

    log("    Calling LLM for mapping analysis...")
    
    try:
        response = client.chat.completions.create(
            model=OLLAMA_MODEL,
            temperature=0.3,
            messages=[
                {"role": "system", "content": "You are a requirements engineering expert. Always respond in valid JSON."},
                {"role": "user", "content": prompt}
            ]
        )
        
        llm_response = response.choices[0].message.content
        
        # Try to parse JSON from response
        try:
            # Find JSON in response
            import re
            json_match = re.search(r'\{[\s\S]*\}', llm_response)
            if json_match:
                mapping = json.loads(json_match.group())
            else:
                mapping = {"raw_response": llm_response}
        except json.JSONDecodeError:
            mapping = {"raw_response": llm_response}
        
        # Create default mapping if LLM response wasn't parseable
        if "mapping" not in mapping:
            mapping = {
                "mapping": [
                    {"source": "1. Project Overview", "target": "1. Introduction", "notes": "Overview maps to Introduction"},
                    {"source": "2. Functional Requirements", "target": "3.2 Functional Requirements", "notes": "Direct mapping"},
                    {"source": "3. Non-Functional Requirements", "target": "3.3-3.5 Performance/Attributes", "notes": "Split across sections"},
                    {"source": "4. Constraints & Assumptions", "target": "2.4-2.5 Constraints/Assumptions", "notes": "Direct mapping"},
                    {"source": "5. Acceptance Criteria", "target": "4. Appendices", "notes": "Move to appendix"}
                ],
                "unmapped_source": [],
                "target_needs_content": ["1.3 Definitions", "1.4 References", "3.1 External Interfaces", "5. Index"],
                "transformation_notes": "Most content maps directly. Some IEEE sections need to be synthesized from source content."
            }
        
        log(f"    Generated {len(mapping.get('mapping', []))} mappings")
        
    except Exception as e:
        log(f"    LLM error: {e}")
        mapping = {
            "mapping": [
                {"source": "Project Overview", "target": "Introduction", "notes": "Standard mapping"},
                {"source": "Functional Requirements", "target": "Specific Requirements", "notes": "Direct mapping"},
                {"source": "Non-Functional Requirements", "target": "System Attributes", "notes": "Split mapping"}
            ],
            "error": str(e)
        }
    
    # Generate human-readable explanation
    explanation = "## Proposed Mapping Strategy\n\n"
    for m in mapping.get("mapping", []):
        explanation += f"- **{m.get('source')}** → **{m.get('target')}**\n"
        explanation += f"  _{m.get('notes', 'No notes')}_\n\n"
    
    if mapping.get("target_needs_content"):
        explanation += "\n### Sections Needing New Content:\n"
        for section in mapping.get("target_needs_content", []):
            explanation += f"- {section}\n"
    
    explanation += f"\n### Overall Strategy:\n{mapping.get('transformation_notes', 'Standard transformation')}\n"
    
    processing_log.append(f"Proposed {len(mapping.get('mapping', []))} mappings")
    
    return {
        "proposed_mapping": mapping,
        "mapping_explanation": explanation,
        "current_step": "step3_analyze_mapping",
        "processing_log": processing_log,
        # Set up for human review
        "human_review_required": True,
        "review_stage": "mapping_review",
        "human_approved": False
    }


# ============================================================
# Human Review Node (Interrupt Point)
# ============================================================

def human_review_mapping(state: TransformState) -> dict:
    """
    Human-in-the-loop: Review proposed mapping before transformation.
    In a real application, this would pause and wait for human input.
    """
    log("\n" + "=" * 60)
    log("HUMAN REVIEW REQUIRED: Mapping Review")
    log("=" * 60)
    
    processing_log = state.processing_log.copy()
    processing_log.append(f"Human review requested: {datetime.now().isoformat()}")
    
    # Display the mapping for human review
    log("\n" + state.mapping_explanation)
    
    log("\n[Awaiting human input...]")
    log("Options: 'approve', 'modify', or provide feedback")
    
    # Simulate human approval for demo
    # In real implementation, this would use LangGraph's interrupt_before
    # or an external callback mechanism
    
    # For demo: auto-approve after showing the mapping
    human_input = "approve"  # Simulated
    
    if human_input.lower() == "approve":
        log("\n[Human approved the mapping]")
        return {
            "human_approved": True,
            "human_feedback": "Mapping approved as proposed",
            "human_review_required": False,
            "current_step": "human_review_mapping",
            "processing_log": processing_log
        }
    else:
        # Would loop back for modification
        return {
            "human_approved": False,
            "human_feedback": human_input,
            "human_review_required": True,
            "current_step": "human_review_mapping",
            "processing_log": processing_log
        }


# ============================================================
# Step 4: Transform Content (Apply Mapping)
# ============================================================

def step4_transform(state: TransformState) -> dict:
    """Transform source content to target template structure."""
    log("\n[Step 4] Transforming content to target format...")
    
    processing_log = state.processing_log.copy()
    processing_log.append(f"Step 4 started: {datetime.now().isoformat()}")
    
    source = state.source_parsed
    mapping = state.proposed_mapping
    
    # Build transformed content structure
    transformed = {
        "1_introduction": {
            "1_1_purpose": f"This Software Requirements Specification (SRS) describes the requirements for the {source.get('title', 'System')}.",
            "1_2_scope": "",
            "1_3_definitions": [],
            "1_4_references": [],
            "1_5_overview": "This document follows the IEEE 830 standard format."
        },
        "2_overall_description": {
            "2_1_product_perspective": "",
            "2_2_product_functions": [],
            "2_3_user_characteristics": [],
            "2_4_constraints": [],
            "2_5_assumptions": []
        },
        "3_specific_requirements": {
            "3_1_external_interfaces": {
                "user_interfaces": [],
                "hardware_interfaces": [],
                "software_interfaces": [],
                "communication_interfaces": []
            },
            "3_2_functional_requirements": [],
            "3_3_performance_requirements": [],
            "3_4_design_constraints": [],
            "3_5_system_attributes": {
                "reliability": [],
                "availability": [],
                "security": [],
                "maintainability": [],
                "portability": []
            }
        },
        "4_appendices": [],
        "5_index": []
    }
    
    # Map source content to transformed structure
    for section in source.get("sections", []):
        section_title = section.get("title", "").lower()
        
        # Project Overview → Introduction
        if "overview" in section_title or "project" in section_title:
            for subsec in section.get("subsections", []):
                subsec_title = subsec.get("title", "").lower()
                items_text = " ".join([str(item.get("text", item.get("description", ""))) for item in subsec.get("items", [])])
                
                if "description" in subsec_title:
                    transformed["1_introduction"]["1_2_scope"] = items_text
                elif "objectives" in subsec_title:
                    transformed["2_overall_description"]["2_2_product_functions"] = [
                        item.get("text", "") for item in subsec.get("items", []) if item.get("text")
                    ]
                elif "stakeholders" in subsec_title:
                    transformed["2_overall_description"]["2_3_user_characteristics"] = [
                        item.get("text", "") for item in subsec.get("items", []) if item.get("text")
                    ]
        
        # Functional Requirements → 3.2
        elif "functional" in section_title and "non" not in section_title:
            for req in source.get("requirements", {}).get("functional", []):
                transformed["3_specific_requirements"]["3_2_functional_requirements"].append({
                    "id": req.get("id", "").replace("FR-", "REQ-"),
                    "description": req.get("description", ""),
                    "original_id": req.get("id", "")
                })
        
        # Non-Functional Requirements → 3.3, 3.5
        elif "non-functional" in section_title or "non functional" in section_title:
            for req in source.get("requirements", {}).get("non_functional", []):
                req_id = req.get("id", "")
                req_desc = req.get("description", "")
                
                if "NFR-P" in req_id:  # Performance
                    transformed["3_specific_requirements"]["3_3_performance_requirements"].append({
                        "id": req_id.replace("NFR-", "PERF-"),
                        "description": req_desc
                    })
                elif "NFR-S" in req_id:  # Security
                    transformed["3_specific_requirements"]["3_5_system_attributes"]["security"].append({
                        "id": req_id.replace("NFR-", "SEC-"),
                        "description": req_desc
                    })
                elif "NFR-A" in req_id:  # Availability
                    transformed["3_specific_requirements"]["3_5_system_attributes"]["availability"].append({
                        "id": req_id.replace("NFR-", "AVAIL-"),
                        "description": req_desc
                    })
                elif "NFR-SC" in req_id:  # Scalability
                    transformed["3_specific_requirements"]["3_5_system_attributes"]["reliability"].append({
                        "id": req_id.replace("NFR-", "SCALE-"),
                        "description": req_desc
                    })
        
        # Constraints & Assumptions → 2.4, 2.5
        elif "constraint" in section_title or "assumption" in section_title:
            for subsec in section.get("subsections", []):
                subsec_title = subsec.get("title", "").lower()
                items = [item.get("text", "") for item in subsec.get("items", []) if item.get("text")]
                
                if "constraint" in subsec_title:
                    transformed["2_overall_description"]["2_4_constraints"].extend(items)
                elif "assumption" in subsec_title:
                    transformed["2_overall_description"]["2_5_assumptions"].extend(items)
        
        # Acceptance Criteria → Appendices
        elif "acceptance" in section_title:
            for subsec in section.get("subsections", []):
                items = [item.get("text", "") for item in subsec.get("items", []) if item.get("text")]
                transformed["4_appendices"].extend(items)
    
    # Count transformed items
    fr_count = len(transformed["3_specific_requirements"]["3_2_functional_requirements"])
    nfr_count = len(transformed["3_specific_requirements"]["3_3_performance_requirements"])
    nfr_count += sum(len(v) for v in transformed["3_specific_requirements"]["3_5_system_attributes"].values() if isinstance(v, list))
    
    log(f"    Transformed {fr_count} functional requirements")
    log(f"    Transformed {nfr_count} non-functional requirements")
    
    processing_log.append(f"Transformed {fr_count} FR, {nfr_count} NFR")
    
    return {
        "transformed_content": transformed,
        "current_step": "step4_transform",
        "processing_log": processing_log
    }


# ============================================================
# Step 5: Validate Transformation
# ============================================================

def step5_validate(state: TransformState) -> dict:
    """Validate the transformed content for completeness and correctness."""
    log("\n[Step 5] Validating transformation...")
    
    processing_log = state.processing_log.copy()
    processing_log.append(f"Step 5 started: {datetime.now().isoformat()}")
    
    transformed = state.transformed_content
    source = state.source_parsed
    
    validation = {
        "passed": True,
        "checks": [],
        "warnings": [],
        "errors": [],
        "coverage": {}
    }
    
    # Check 1: All functional requirements mapped
    source_fr = len(source.get("requirements", {}).get("functional", []))
    target_fr = len(transformed.get("3_specific_requirements", {}).get("3_2_functional_requirements", []))
    
    validation["checks"].append({
        "name": "Functional Requirements Coverage",
        "source_count": source_fr,
        "target_count": target_fr,
        "passed": source_fr == target_fr
    })
    
    if source_fr != target_fr:
        validation["warnings"].append(f"FR count mismatch: {source_fr} source vs {target_fr} target")
    
    # Check 2: Non-functional requirements mapped
    source_nfr = len(source.get("requirements", {}).get("non_functional", []))
    target_nfr = len(transformed.get("3_specific_requirements", {}).get("3_3_performance_requirements", []))
    for attr in transformed.get("3_specific_requirements", {}).get("3_5_system_attributes", {}).values():
        if isinstance(attr, list):
            target_nfr += len(attr)
    
    validation["checks"].append({
        "name": "Non-Functional Requirements Coverage",
        "source_count": source_nfr,
        "target_count": target_nfr,
        "passed": source_nfr == target_nfr
    })
    
    if source_nfr != target_nfr:
        validation["warnings"].append(f"NFR count mismatch: {source_nfr} source vs {target_nfr} target")
    
    # Check 3: Required sections have content
    required_sections = ["1_2_scope", "2_2_product_functions", "3_2_functional_requirements"]
    for section in required_sections:
        has_content = False
        if section in transformed.get("1_introduction", {}):
            has_content = bool(transformed["1_introduction"][section])
        elif section in transformed.get("2_overall_description", {}):
            has_content = bool(transformed["2_overall_description"][section])
        elif section in transformed.get("3_specific_requirements", {}):
            has_content = bool(transformed["3_specific_requirements"][section])
        
        validation["checks"].append({
            "name": f"Section {section} has content",
            "passed": has_content
        })
        
        if not has_content:
            validation["warnings"].append(f"Section {section} is empty")
    
    # Calculate overall coverage
    total_checks = len(validation["checks"])
    passed_checks = sum(1 for c in validation["checks"] if c.get("passed"))
    validation["coverage"]["percentage"] = round(passed_checks / total_checks * 100, 1) if total_checks > 0 else 0
    validation["coverage"]["passed"] = passed_checks
    validation["coverage"]["total"] = total_checks
    
    validation["passed"] = len(validation["errors"]) == 0
    
    log(f"    Validation checks: {passed_checks}/{total_checks} passed")
    log(f"    Coverage: {validation['coverage']['percentage']}%")
    if validation["warnings"]:
        log(f"    Warnings: {len(validation['warnings'])}")
    
    processing_log.append(f"Validation: {validation['coverage']['percentage']}% coverage")
    
    return {
        "validation_results": validation,
        "current_step": "step5_validate",
        "processing_log": processing_log,
        # Set up for human approval
        "human_review_required": True,
        "review_stage": "final_approval",
        "human_approved": False
    }


# ============================================================
# Human Approval Node (Final Approval)
# ============================================================

def human_approval_final(state: TransformState) -> dict:
    """
    Human-in-the-loop: Final approval before generating output.
    """
    log("\n" + "=" * 60)
    log("HUMAN APPROVAL REQUIRED: Final Output Review")
    log("=" * 60)
    
    processing_log = state.processing_log.copy()
    processing_log.append(f"Final approval requested: {datetime.now().isoformat()}")
    
    validation = state.validation_results
    
    log(f"\nValidation Summary:")
    log(f"  - Coverage: {validation.get('coverage', {}).get('percentage', 0)}%")
    log(f"  - Checks passed: {validation.get('coverage', {}).get('passed', 0)}/{validation.get('coverage', {}).get('total', 0)}")
    
    if validation.get("warnings"):
        log(f"\nWarnings:")
        for warning in validation.get("warnings", []):
            log(f"  - {warning}")
    
    log("\n[Awaiting human approval...]")
    log("Options: 'approve' to generate final document, 'reject' to stop")
    
    # Simulate human approval for demo
    human_input = "approve"  # Simulated
    
    if human_input.lower() == "approve":
        log("\n[Human approved - proceeding to generate output]")
        return {
            "human_approved": True,
            "human_feedback": "Final output approved",
            "human_review_required": False,
            "current_step": "human_approval_final",
            "processing_log": processing_log
        }
    else:
        log("\n[Human rejected - pipeline will end]")
        return {
            "human_approved": False,
            "human_feedback": human_input,
            "human_review_required": False,
            "current_step": "human_approval_final",
            "processing_log": processing_log
        }


# ============================================================
# Step 6: Generate Final Output Document
# ============================================================

def step6_generate_output(state: TransformState) -> dict:
    """Generate the final transformed requirements document."""
    log("\n[Step 6] Generating final output document...")
    
    processing_log = state.processing_log.copy()
    processing_log.append(f"Step 6 started: {datetime.now().isoformat()}")
    
    transformed = state.transformed_content
    source = state.source_parsed
    
    # Build the final document in IEEE 830 format
    doc = []
    doc.append("# IEEE 830 Software Requirements Specification")
    doc.append(f"\n**Project:** {source.get('title', 'System')}")
    doc.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    doc.append(f"**Run ID:** `{state.run_id}`")
    doc.append(f"**Source Version:** {source.get('version', 'N/A')}")
    doc.append(f"**Platform:** {state.platform_info.get('summary', 'Unknown')}")
    doc.append("\n---\n")
    
    # 1. Introduction
    doc.append("## 1. Introduction")
    doc.append("\n### 1.1 Purpose")
    doc.append(transformed["1_introduction"]["1_1_purpose"])
    
    doc.append("\n### 1.2 Scope")
    doc.append(transformed["1_introduction"]["1_2_scope"] or "[Scope to be defined]")
    
    doc.append("\n### 1.3 Definitions, Acronyms, and Abbreviations")
    doc.append("| Term | Definition |")
    doc.append("|------|------------|")
    doc.append("| CRM | Customer Relationship Management |")
    doc.append("| SRS | Software Requirements Specification |")
    doc.append("| FR | Functional Requirement |")
    doc.append("| NFR | Non-Functional Requirement |")
    doc.append("| API | Application Programming Interface |")
    
    doc.append("\n### 1.4 References")
    doc.append("- IEEE 830-1998: Recommended Practice for Software Requirements Specifications")
    doc.append("- Source Requirements Document v" + source.get("version", "1.0"))
    
    doc.append("\n### 1.5 Overview")
    doc.append(transformed["1_introduction"]["1_5_overview"])
    
    # 2. Overall Description
    doc.append("\n## 2. Overall Description")
    
    doc.append("\n### 2.1 Product Perspective")
    doc.append("This system is a new development intended to replace the existing legacy CRM solution.")
    
    doc.append("\n### 2.2 Product Functions")
    for func in transformed["2_overall_description"]["2_2_product_functions"]:
        doc.append(f"- {func}")
    
    doc.append("\n### 2.3 User Characteristics")
    for user in transformed["2_overall_description"]["2_3_user_characteristics"]:
        doc.append(f"- {user}")
    
    doc.append("\n### 2.4 Constraints")
    for constraint in transformed["2_overall_description"]["2_4_constraints"]:
        doc.append(f"- {constraint}")
    
    doc.append("\n### 2.5 Assumptions and Dependencies")
    for assumption in transformed["2_overall_description"]["2_5_assumptions"]:
        doc.append(f"- {assumption}")
    
    # 3. Specific Requirements
    doc.append("\n## 3. Specific Requirements")
    
    doc.append("\n### 3.1 External Interface Requirements")
    doc.append("\n#### 3.1.1 User Interfaces")
    doc.append("- Web-based interface accessible via modern browsers")
    doc.append("- Mobile-responsive design for field access")
    
    doc.append("\n#### 3.1.2 Hardware Interfaces")
    doc.append("- Standard desktop/laptop hardware")
    doc.append("- Mobile devices (iOS, Android)")
    
    doc.append("\n#### 3.1.3 Software Interfaces")
    doc.append("- ERP Integration (SAP)")
    doc.append("- Email Integration (Microsoft 365)")
    doc.append("- Active Directory for authentication")
    
    doc.append("\n#### 3.1.4 Communication Interfaces")
    doc.append("- HTTPS/TLS 1.3 for all communications")
    doc.append("- REST API for third-party integrations")
    
    doc.append("\n### 3.2 Functional Requirements")
    for i, req in enumerate(transformed["3_specific_requirements"]["3_2_functional_requirements"], 1):
        doc.append(f"\n**{req['id']}**: {req['description']}")
        doc.append(f"  - _Original ID: {req.get('original_id', 'N/A')}_")
    
    doc.append("\n### 3.3 Performance Requirements")
    for req in transformed["3_specific_requirements"]["3_3_performance_requirements"]:
        doc.append(f"- **{req['id']}**: {req['description']}")
    
    doc.append("\n### 3.4 Design Constraints")
    doc.append("- Must run on Azure cloud infrastructure")
    doc.append("- Must use PostgreSQL database")
    doc.append("- Must support modern browsers (Chrome, Firefox, Edge, Safari)")
    
    doc.append("\n### 3.5 Software System Attributes")
    
    doc.append("\n#### 3.5.1 Reliability")
    for req in transformed["3_specific_requirements"]["3_5_system_attributes"]["reliability"]:
        doc.append(f"- **{req['id']}**: {req['description']}")
    
    doc.append("\n#### 3.5.2 Availability")
    for req in transformed["3_specific_requirements"]["3_5_system_attributes"]["availability"]:
        doc.append(f"- **{req['id']}**: {req['description']}")
    
    doc.append("\n#### 3.5.3 Security")
    for req in transformed["3_specific_requirements"]["3_5_system_attributes"]["security"]:
        doc.append(f"- **{req['id']}**: {req['description']}")
    
    doc.append("\n#### 3.5.4 Maintainability")
    doc.append("- System shall support hot-patching without downtime")
    doc.append("- System shall provide comprehensive logging for troubleshooting")
    
    doc.append("\n#### 3.5.5 Portability")
    doc.append("- System shall be containerized for deployment flexibility")
    doc.append("- System shall not have vendor-specific dependencies")
    
    # 4. Appendices
    doc.append("\n## 4. Appendices")
    doc.append("\n### Appendix A: Acceptance Criteria")
    for item in transformed["4_appendices"]:
        doc.append(f"- {item}")
    
    # 5. Index
    doc.append("\n## 5. Index")
    doc.append("\n| Term | Section |")
    doc.append("|------|---------|")
    doc.append("| Authentication | 3.2 |")
    doc.append("| Performance | 3.3 |")
    doc.append("| Security | 3.5.3 |")
    doc.append("| Availability | 3.5.2 |")
    
    # Join document
    final_document = "\n".join(doc)
    
    # Save to file with unique GUID in filename
    output_file = generate_output_filename(state.run_id)
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(final_document)
    
    log(f"    Generated document: {len(final_document)} characters")
    log(f"    Run ID: {state.run_id}")
    log(f"    Saved to: {output_file}")
    
    processing_log.append(f"Generated {output_file}")
    
    return {
        "final_document": final_document,
        "output_file": output_file,
        "current_step": "step6_generate_output",
        "processing_log": processing_log
    }


# ============================================================
# Routing Functions
# ============================================================

def route_after_mapping_review(state: TransformState) -> str:
    """Route after human reviews the mapping."""
    if state.human_approved:
        return "transform"
    return "revise_mapping"  # Would loop back to step 3

def route_after_final_approval(state: TransformState) -> str:
    """Route after human final approval."""
    if state.human_approved:
        return "generate"
    return "end"  # Stop pipeline if not approved


# ============================================================
# Build the Pipeline Graph
# ============================================================

def create_transformer_pipeline():
    """
    Create the requirements transformation pipeline with human-in-the-loop.
    
    Flow:
    START → step1_load_source → step2_load_template → step3_analyze_mapping 
          → [human_review_mapping] → step4_transform → step5_validate 
          → [human_approval_final] → step6_generate_output → END
    """
    builder = StateGraph(TransformState)
    
    # Add all nodes
    builder.add_node("step1_load_source", step1_load_source)
    builder.add_node("step2_load_template", step2_load_template)
    builder.add_node("step3_analyze_mapping", step3_analyze_mapping)
    builder.add_node("human_review_mapping", human_review_mapping)
    builder.add_node("step4_transform", step4_transform)
    builder.add_node("step5_validate", step5_validate)
    builder.add_node("human_approval_final", human_approval_final)
    builder.add_node("step6_generate_output", step6_generate_output)
    
    # Define flow
    builder.add_edge(START, "step1_load_source")
    builder.add_edge("step1_load_source", "step2_load_template")
    builder.add_edge("step2_load_template", "step3_analyze_mapping")
    builder.add_edge("step3_analyze_mapping", "human_review_mapping")
    
    # After human review, route based on approval
    builder.add_conditional_edges(
        "human_review_mapping",
        route_after_mapping_review,
        {
            "transform": "step4_transform",
            "revise_mapping": "step3_analyze_mapping"  # Loop back
        }
    )
    
    builder.add_edge("step4_transform", "step5_validate")
    builder.add_edge("step5_validate", "human_approval_final")
    
    # After final approval, route based on approval
    builder.add_conditional_edges(
        "human_approval_final",
        route_after_final_approval,
        {
            "generate": "step6_generate_output",
            "end": END
        }
    )
    
    builder.add_edge("step6_generate_output", END)
    
    return builder.compile()


# ============================================================
# Main Execution
# ============================================================

def main():
    """Run the requirements transformation pipeline."""
    
    # Generate unique run ID
    run_id = generate_run_id()
    
    log("=" * 70)
    log("LangGraph Advanced Example: Requirements Document Transformer")
    log("=" * 70)
    
    # Display platform info
    log(f"\nPlatform: {PLATFORM_INFO['summary']}")
    if PLATFORM_INFO["is_arm"]:
        log("  Architecture: ARM (detected)")
    if PLATFORM_INFO["is_windows"]:
        log("  OS: Windows")
    elif PLATFORM_INFO["is_linux"]:
        log("  OS: Linux")
    elif PLATFORM_INFO["is_macos"]:
        log("  OS: macOS")
    
    log(f"\nRun ID: {run_id}")
    log("\nThis pipeline transforms a generic requirements document to IEEE 830 format")
    log("with human-in-the-loop review at key decision points.\n")
    
    # Check Ollama
    log("Checking Ollama connection...")
    try:
        get_client().models.list()
        log("Ollama connected!\n")
    except Exception as e:
        log(f"Warning: Ollama not available ({e})")
        log("Pipeline will use fallback mappings.\n")
    
    # Create and run pipeline
    pipeline = create_transformer_pipeline()
    
    log("-" * 70)
    log("Starting transformation pipeline...")
    log("-" * 70)
    
    # Initialize state with run_id and platform info
    initial_state = TransformState(
        run_id=run_id,
        platform_info=PLATFORM_INFO
    )
    
    try:
        result = pipeline.invoke(initial_state)
        
        log("\n" + "=" * 70)
        log("PIPELINE COMPLETE")
        log("=" * 70)
        
        log(f"\nOutput file: {result.get('output_file', 'N/A')}")
        log(f"Processing steps: {len(result.get('processing_log', []))}")
        
        # Show summary
        if result.get("validation_results"):
            val = result["validation_results"]
            log(f"\nValidation Summary:")
            log(f"  Coverage: {val.get('coverage', {}).get('percentage', 0)}%")
            log(f"  Checks: {val.get('coverage', {}).get('passed', 0)}/{val.get('coverage', {}).get('total', 0)}")
        
        log("\nTransformation complete!")
        log(f"Review the output at: {result.get('output_file', 'transformed_requirements_ieee830.md')}")
        
    except Exception as e:
        log(f"\nPipeline error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

