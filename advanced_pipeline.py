"""
LangGraph Advanced Example: Document Processing Pipeline

This example demonstrates a multi-step document processing pipeline:
1. Load document (simulate PDF/file input)
2. Parse to structured JSON
3. Extract sections and subsections
4. Generate comparison prompts
5. Run LLM analysis
6. Seed schema with results
7. Merge and finalize output

Uses Ollama for local LLM processing.

Key LangGraph concepts demonstrated:
- Complex multi-node pipelines
- State accumulation across steps
- Conditional branching
- Error handling nodes
- Parallel processing simulation
"""

import warnings
# Suppress Pydantic V1 deprecation warnings for Python 3.14+
warnings.filterwarnings("ignore", category=UserWarning, module="langchain_core.*")

import sys
import json
import re
from typing import Literal, Optional
from datetime import datetime
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, START, END
from openai import OpenAI

# ============================================================
# Configuration
# ============================================================

OLLAMA_BASE_URL = "http://localhost:11434/v1"
OLLAMA_MODEL = "llama3.2:1b"

def log(msg: str):
    print(msg)
    sys.stdout.flush()

def get_client():
    return OpenAI(base_url=OLLAMA_BASE_URL, api_key="ollama")

# ============================================================
# Pipeline State - Accumulates data through all steps
# ============================================================

class Section(BaseModel):
    """A document section with subsections"""
    title: str = ""
    content: str = ""
    subsections: list[str] = Field(default_factory=list)

class PipelineState(BaseModel):
    """
    Complete state for the document processing pipeline.
    Each step adds to or transforms this state.
    """
    # Input
    input_file: str = Field(default="", description="Path or content of input file")
    
    # Step 1: Raw document
    raw_content: str = Field(default="", description="Raw document content")
    
    # Step 2: Parsed JSON
    parsed_json: dict = Field(default_factory=dict, description="Structured JSON from document")
    
    # Step 3: Extracted sections
    sections: list[dict] = Field(default_factory=list, description="Extracted sections")
    
    # Step 4: Comparison prompts
    comparison_prompts: list[dict] = Field(default_factory=list, description="Generated prompts for LLM")
    
    # Step 5: LLM responses
    llm_responses: list[dict] = Field(default_factory=list, description="LLM analysis results")
    
    # Step 6: Schema with seeded data
    schema_data: dict = Field(default_factory=dict, description="Schema populated with extracted data")
    
    # Step 7: Final merged output
    final_output: dict = Field(default_factory=dict, description="Final merged result")
    
    # Metadata
    current_step: str = Field(default="", description="Current processing step")
    errors: list[str] = Field(default_factory=list, description="Any errors encountered")
    processing_log: list[str] = Field(default_factory=list, description="Processing history")
    started_at: str = Field(default="", description="Pipeline start time")
    completed_at: str = Field(default="", description="Pipeline completion time")
    
    # Retry/Recovery fields
    retry_count: int = Field(default=0, description="Current retry attempt")
    max_retries: int = Field(default=3, description="Maximum retries per step")
    last_successful_step: str = Field(default="", description="Last step that completed successfully")
    failed_step: str = Field(default="", description="Step that failed")
    should_retry: bool = Field(default=False, description="Flag to trigger retry")
    should_rollback: bool = Field(default=False, description="Flag to rollback to previous step")


# ============================================================
# Step 1: Load Document (Simulates PDF/File Loading)
# ============================================================

def step1_load_document(state: PipelineState) -> dict:
    """
    Step 1: Load and read the input document.
    In production, this would use PyPDF2, pdfplumber, etc.
    """
    log("\n[Step 1] Loading document...")
    
    processing_log = state.processing_log.copy()
    processing_log.append(f"Step 1 started: {datetime.now().isoformat()}")
    
    # Simulate loading a document (in production, read actual file)
    # For demo, we'll use sample content
    if state.input_file:
        raw_content = state.input_file
    else:
        # Sample document for demonstration
        raw_content = """
# Project Requirements Document

## 1. Overview
This document outlines the requirements for the new Customer Portal system.
The portal will serve as the primary interface for customer interactions.

## 2. Functional Requirements

### 2.1 User Authentication
- Users must be able to register with email
- Password requirements: 8+ characters, 1 number, 1 special char
- Support for OAuth (Google, Microsoft)

### 2.2 Dashboard
- Display account summary
- Show recent transactions
- Notification center

### 2.3 Account Management
- Profile editing
- Password reset
- Two-factor authentication setup

## 3. Non-Functional Requirements

### 3.1 Performance
- Page load time < 2 seconds
- Support 10,000 concurrent users
- 99.9% uptime SLA

### 3.2 Security
- All data encrypted at rest
- TLS 1.3 for transit
- Annual security audits

## 4. Timeline
- Phase 1: Q1 2025 - Authentication & Dashboard
- Phase 2: Q2 2025 - Account Management
- Phase 3: Q3 2025 - Full Launch
"""
    
    log(f"    Loaded {len(raw_content)} characters")
    processing_log.append(f"Loaded document: {len(raw_content)} chars")
    
    return {
        "raw_content": raw_content,
        "current_step": "step1_load",
        "last_successful_step": "step1_load",
        "processing_log": processing_log,
        "started_at": datetime.now().isoformat(),
        "retry_count": 0  # Reset on success
    }


# ============================================================
# Step 2: Parse to Structured JSON
# ============================================================

def step2_parse_to_json(state: PipelineState) -> dict:
    """
    Step 2: Parse raw document into structured JSON.
    Identifies headers, sections, and content blocks.
    """
    log("\n[Step 2] Parsing to structured JSON...")
    
    processing_log = state.processing_log.copy()
    processing_log.append(f"Step 2 started: {datetime.now().isoformat()}")
    
    content = state.raw_content
    
    # Parse markdown-style document into structure
    parsed = {
        "title": "",
        "sections": [],
        "metadata": {
            "parsed_at": datetime.now().isoformat(),
            "total_lines": len(content.split('\n'))
        }
    }
    
    current_section = None
    current_subsection = None
    
    for line in content.split('\n'):
        line = line.strip()
        
        # Main title (# Header)
        if line.startswith('# ') and not line.startswith('## '):
            parsed["title"] = line[2:].strip()
        
        # Section (## Header)
        elif line.startswith('## '):
            if current_section:
                parsed["sections"].append(current_section)
            current_section = {
                "title": line[3:].strip(),
                "content": "",
                "subsections": []
            }
            current_subsection = None
        
        # Subsection (### Header)
        elif line.startswith('### '):
            if current_section:
                current_subsection = {
                    "title": line[4:].strip(),
                    "items": []
                }
                current_section["subsections"].append(current_subsection)
        
        # List item
        elif line.startswith('- '):
            if current_subsection:
                current_subsection["items"].append(line[2:].strip())
            elif current_section:
                current_section["content"] += line + "\n"
        
        # Regular content
        elif line and current_section:
            current_section["content"] += line + "\n"
    
    # Don't forget the last section
    if current_section:
        parsed["sections"].append(current_section)
    
    log(f"    Parsed {len(parsed['sections'])} sections")
    processing_log.append(f"Parsed {len(parsed['sections'])} sections")
    
    return {
        "parsed_json": parsed,
        "current_step": "step2_parse",
        "last_successful_step": "step2_parse",
        "processing_log": processing_log,
        "retry_count": 0
    }


# ============================================================
# Step 3: Extract Sections and Subsections
# ============================================================

def step3_extract_sections(state: PipelineState) -> dict:
    """
    Step 3: Extract and normalize all sections/subsections.
    Creates a flat list for easier processing.
    """
    log("\n[Step 3] Extracting sections and subsections...")
    
    processing_log = state.processing_log.copy()
    processing_log.append(f"Step 3 started: {datetime.now().isoformat()}")
    
    sections = []
    parsed = state.parsed_json
    
    for section in parsed.get("sections", []):
        section_data = {
            "type": "section",
            "title": section.get("title", ""),
            "content": section.get("content", "").strip(),
            "subsection_count": len(section.get("subsections", []))
        }
        sections.append(section_data)
        
        for subsection in section.get("subsections", []):
            subsection_data = {
                "type": "subsection",
                "parent": section.get("title", ""),
                "title": subsection.get("title", ""),
                "items": subsection.get("items", []),
                "item_count": len(subsection.get("items", []))
            }
            sections.append(subsection_data)
    
    log(f"    Extracted {len(sections)} total sections/subsections")
    processing_log.append(f"Extracted {len(sections)} items")
    
    return {
        "sections": sections,
        "current_step": "step3_extract",
        "last_successful_step": "step3_extract",
        "processing_log": processing_log,
        "retry_count": 0
    }


# ============================================================
# Step 4: Generate Comparison/Analysis Prompts
# ============================================================

def step4_generate_prompts(state: PipelineState) -> dict:
    """
    Step 4: Generate prompts for LLM analysis.
    Creates targeted prompts for each section.
    """
    log("\n[Step 4] Generating analysis prompts...")
    
    processing_log = state.processing_log.copy()
    processing_log.append(f"Step 4 started: {datetime.now().isoformat()}")
    
    prompts = []
    
    for section in state.sections:
        if section["type"] == "section":
            prompt = f"""Analyze the following document section and provide:
1. A brief summary (2-3 sentences)
2. Key requirements or points (bullet list)
3. Priority level (High/Medium/Low)
4. Any potential risks or concerns

Section: {section['title']}
Content: {section['content'][:500]}..."""
            prompts.append({
                "section": section["title"],
                "prompt": prompt,
                "type": "section_analysis"
            })
        
        elif section["type"] == "subsection" and section.get("items"):
            items_text = "\n".join(f"- {item}" for item in section["items"][:5])
            prompt = f"""Review these requirements and provide:
1. Feasibility assessment
2. Implementation complexity (Simple/Medium/Complex)
3. Dependencies on other features
4. Estimated effort (hours)

Subsection: {section['title']}
Parent Section: {section['parent']}
Requirements:
{items_text}"""
            prompts.append({
                "section": section["title"],
                "parent": section["parent"],
                "prompt": prompt,
                "type": "requirement_analysis"
            })
    
    log(f"    Generated {len(prompts)} prompts")
    processing_log.append(f"Generated {len(prompts)} prompts")
    
    return {
        "comparison_prompts": prompts,
        "current_step": "step4_prompts",
        "last_successful_step": "step4_prompts",
        "processing_log": processing_log,
        "retry_count": 0
    }


# ============================================================
# Step 5: Run LLM Analysis
# ============================================================

def step5_run_llm(state: PipelineState) -> dict:
    """
    Step 5: Execute LLM analysis for each prompt.
    Uses Ollama for local processing.
    """
    log("\n[Step 5] Running LLM analysis...")
    
    processing_log = state.processing_log.copy()
    processing_log.append(f"Step 5 started: {datetime.now().isoformat()}")
    
    responses = []
    client = get_client()
    
    # Process first 3 prompts for demo (to save time)
    prompts_to_process = state.comparison_prompts[:3]
    
    for i, prompt_data in enumerate(prompts_to_process):
        log(f"    Processing prompt {i+1}/{len(prompts_to_process)}: {prompt_data['section']}")
        
        try:
            response = client.chat.completions.create(
                model=OLLAMA_MODEL,
                temperature=0.3,
                messages=[
                    {"role": "system", "content": "You are a technical analyst. Provide concise, structured analysis. Respond in JSON format."},
                    {"role": "user", "content": prompt_data["prompt"]}
                ]
            )
            
            llm_response = response.choices[0].message.content
            
            # Try to parse as JSON, otherwise wrap in structure
            try:
                parsed_response = json.loads(llm_response)
            except:
                parsed_response = {"raw_analysis": llm_response}
            
            responses.append({
                "section": prompt_data["section"],
                "type": prompt_data["type"],
                "analysis": parsed_response,
                "processed_at": datetime.now().isoformat()
            })
            
        except Exception as e:
            log(f"    Error processing {prompt_data['section']}: {str(e)}")
            responses.append({
                "section": prompt_data["section"],
                "type": prompt_data["type"],
                "error": str(e),
                "processed_at": datetime.now().isoformat()
            })
    
    log(f"    Completed {len(responses)} LLM analyses")
    processing_log.append(f"LLM analyzed {len(responses)} sections")
    
    return {
        "llm_responses": responses,
        "current_step": "step5_llm",
        "last_successful_step": "step5_llm",
        "processing_log": processing_log,
        "retry_count": 0
    }


# ============================================================
# Step 6: Seed Schema with Results
# ============================================================

def step6_seed_schema(state: PipelineState) -> dict:
    """
    Step 6: Create a schema and seed it with extracted data.
    Builds the output structure.
    """
    log("\n[Step 6] Seeding schema with results...")
    
    processing_log = state.processing_log.copy()
    processing_log.append(f"Step 6 started: {datetime.now().isoformat()}")
    
    # Create comprehensive schema
    schema = {
        "document": {
            "title": state.parsed_json.get("title", "Untitled"),
            "processed_at": datetime.now().isoformat(),
            "total_sections": len(state.parsed_json.get("sections", [])),
            "total_items_analyzed": len(state.sections)
        },
        "sections_summary": [],
        "llm_analyses": [],
        "statistics": {
            "sections_count": 0,
            "subsections_count": 0,
            "total_requirements": 0
        }
    }
    
    # Populate sections summary
    for section in state.sections:
        if section["type"] == "section":
            schema["statistics"]["sections_count"] += 1
            schema["sections_summary"].append({
                "title": section["title"],
                "has_subsections": section["subsection_count"] > 0,
                "subsection_count": section["subsection_count"]
            })
        else:
            schema["statistics"]["subsections_count"] += 1
            schema["statistics"]["total_requirements"] += section.get("item_count", 0)
    
    # Add LLM analyses
    for response in state.llm_responses:
        if "error" not in response:
            schema["llm_analyses"].append({
                "section": response["section"],
                "analysis_type": response["type"],
                "result": response["analysis"]
            })
    
    log(f"    Schema populated with {len(schema['llm_analyses'])} analyses")
    processing_log.append(f"Schema seeded with {len(schema['llm_analyses'])} analyses")
    
    return {
        "schema_data": schema,
        "current_step": "step6_seed",
        "last_successful_step": "step6_seed",
        "processing_log": processing_log,
        "retry_count": 0
    }


# ============================================================
# Step 7: Merge and Finalize
# ============================================================

def step7_merge_finalize(state: PipelineState) -> dict:
    """
    Step 7: Merge all results into final output.
    Consolidates everything into a comprehensive report.
    """
    log("\n[Step 7] Merging and finalizing output...")
    
    processing_log = state.processing_log.copy()
    processing_log.append(f"Step 7 started: {datetime.now().isoformat()}")
    
    final_output = {
        "report": {
            "title": f"Analysis Report: {state.schema_data.get('document', {}).get('title', 'Document')}",
            "generated_at": datetime.now().isoformat(),
            "pipeline_version": "1.0.0"
        },
        "summary": {
            "document_title": state.schema_data.get("document", {}).get("title"),
            "total_sections": state.schema_data.get("statistics", {}).get("sections_count", 0),
            "total_subsections": state.schema_data.get("statistics", {}).get("subsections_count", 0),
            "total_requirements": state.schema_data.get("statistics", {}).get("total_requirements", 0),
            "analyses_performed": len(state.schema_data.get("llm_analyses", []))
        },
        "detailed_analysis": state.schema_data.get("llm_analyses", []),
        "sections_overview": state.schema_data.get("sections_summary", []),
        "processing_metadata": {
            "started_at": state.started_at,
            "completed_at": datetime.now().isoformat(),
            "steps_completed": len(processing_log),
            "processing_log": processing_log
        }
    }
    
    processing_log.append(f"Step 7 completed: {datetime.now().isoformat()}")
    
    log(f"    Final report generated")
    log(f"    Total sections: {final_output['summary']['total_sections']}")
    log(f"    Total requirements: {final_output['summary']['total_requirements']}")
    log(f"    LLM analyses: {final_output['summary']['analyses_performed']}")
    
    return {
        "final_output": final_output,
        "current_step": "step7_merge",
        "last_successful_step": "step7_merge",
        "completed_at": datetime.now().isoformat(),
        "processing_log": processing_log,
        "retry_count": 0
    }


# ============================================================
# Error Handler Node with Retry Logic
# ============================================================

def handle_error(state: PipelineState) -> dict:
    """
    Handle errors with retry and rollback logic.
    - If retries available: increment counter and set retry flag
    - If max retries reached: attempt rollback to previous step
    - If rollback fails: mark as failed
    """
    log("\n[Error Handler] Processing error...")
    
    errors = state.errors.copy()
    processing_log = state.processing_log.copy()
    retry_count = state.retry_count
    
    failed_step = state.current_step or state.failed_step
    errors.append(f"Error at step: {failed_step} (attempt {retry_count + 1})")
    processing_log.append(f"Error handler triggered for {failed_step}")
    
    # Check if we can retry
    if retry_count < state.max_retries:
        log(f"    Retry {retry_count + 1}/{state.max_retries} - will retry {failed_step}")
        processing_log.append(f"Scheduling retry {retry_count + 1} for {failed_step}")
        return {
            "errors": errors,
            "processing_log": processing_log,
            "retry_count": retry_count + 1,
            "should_retry": True,
            "should_rollback": False,
            "failed_step": failed_step
        }
    
    # Max retries reached - try rollback
    if state.last_successful_step:
        log(f"    Max retries reached. Rolling back to {state.last_successful_step}")
        processing_log.append(f"Rolling back to {state.last_successful_step}")
        return {
            "errors": errors,
            "processing_log": processing_log,
            "retry_count": 0,  # Reset for rollback
            "should_retry": False,
            "should_rollback": True,
            "failed_step": failed_step
        }
    
    # No rollback possible - fail
    log("    No recovery possible. Pipeline failed.")
    processing_log.append("Pipeline failed - no recovery possible")
    return {
        "errors": errors,
        "processing_log": processing_log,
        "current_step": "failed",
        "should_retry": False,
        "should_rollback": False
    }


def retry_router(state: PipelineState) -> dict:
    """
    Router node that decides where to go after error handling.
    Routes to retry the failed step or rollback to previous step.
    """
    log("\n[Retry Router] Determining next action...")
    
    processing_log = state.processing_log.copy()
    
    if state.should_retry:
        log(f"    -> Retrying: {state.failed_step}")
        processing_log.append(f"Retrying {state.failed_step}")
        return {
            "processing_log": processing_log,
            "should_retry": False,
            "current_step": state.failed_step
        }
    
    if state.should_rollback:
        log(f"    -> Rolling back to: {state.last_successful_step}")
        processing_log.append(f"Rolling back to {state.last_successful_step}")
        return {
            "processing_log": processing_log,
            "should_rollback": False,
            "current_step": state.last_successful_step,
            "retry_count": 0
        }
    
    # No action - proceed to end
    log("    -> No recovery action, ending pipeline")
    return {"processing_log": processing_log}


# ============================================================
# Routing Functions (with retry/rollback support)
# ============================================================

def route_after_load(state: PipelineState) -> Literal["parse", "error"]:
    """Route after document loading."""
    if state.raw_content:
        return "parse"
    return "error"

def route_after_parse(state: PipelineState) -> Literal["extract", "error"]:
    """Route after parsing."""
    if state.parsed_json.get("sections"):
        return "extract"
    return "error"

def route_after_llm(state: PipelineState) -> Literal["seed", "error"]:
    """Route after LLM processing."""
    if state.llm_responses:
        return "seed"
    return "error"

def route_after_error(state: PipelineState) -> str:
    """
    Route after error handling - determines retry, rollback, or end.
    Returns the node to transition to.
    """
    if state.should_retry:
        # Retry the failed step
        return state.failed_step or "end"
    
    if state.should_rollback:
        # Go back to last successful step
        return state.last_successful_step or "end"
    
    # No recovery possible
    return "end"


# ============================================================
# Build the Pipeline Graph
# ============================================================

def create_pipeline():
    """
    Create the document processing pipeline with retry/rollback support.
    
    Flow:
    START → step1_load → step2_parse → step3_extract → step4_prompts 
         → step5_llm → step6_seed → step7_merge → END
    
    With error handling and retry/rollback:
    - On error: go to error_handler
    - error_handler decides: retry current step, rollback to previous, or end
    - Retry loops back to the failed step
    - Rollback loops back to last successful step
    """
    builder = StateGraph(PipelineState)
    
    # Add all processing nodes
    builder.add_node("step1_load", step1_load_document)
    builder.add_node("step2_parse", step2_parse_to_json)
    builder.add_node("step3_extract", step3_extract_sections)
    builder.add_node("step4_prompts", step4_generate_prompts)
    builder.add_node("step5_llm", step5_run_llm)
    builder.add_node("step6_seed", step6_seed_schema)
    builder.add_node("step7_merge", step7_merge_finalize)
    builder.add_node("error_handler", handle_error)
    builder.add_node("retry_router", retry_router)
    
    # Define the main flow
    builder.add_edge(START, "step1_load")
    
    # Conditional routing with error handling
    builder.add_conditional_edges(
        "step1_load",
        route_after_load,
        {"parse": "step2_parse", "error": "error_handler"}
    )
    
    builder.add_conditional_edges(
        "step2_parse",
        route_after_parse,
        {"extract": "step3_extract", "error": "error_handler"}
    )
    
    # Linear flow for remaining steps
    builder.add_edge("step3_extract", "step4_prompts")
    builder.add_edge("step4_prompts", "step5_llm")
    
    builder.add_conditional_edges(
        "step5_llm",
        route_after_llm,
        {"seed": "step6_seed", "error": "error_handler"}
    )
    
    builder.add_edge("step6_seed", "step7_merge")
    builder.add_edge("step7_merge", END)
    
    # Error handler routes to retry_router
    builder.add_edge("error_handler", "retry_router")
    
    # Retry router decides: retry step, rollback, or end
    builder.add_conditional_edges(
        "retry_router",
        route_after_error,
        {
            # Retry any step
            "step1_load": "step1_load",
            "step2_parse": "step2_parse",
            "step3_extract": "step3_extract",
            "step4_prompts": "step4_prompts",
            "step5_llm": "step5_llm",
            "step6_seed": "step6_seed",
            "step7_merge": "step7_merge",
            # End pipeline
            "end": END
        }
    )
    
    return builder.compile()


# ============================================================
# Run the Pipeline
# ============================================================

def check_ollama():
    try:
        get_client().models.list()
        return True
    except:
        return False

def main():
    """Run the document processing pipeline."""
    
    log("=" * 60)
    log("LangGraph Advanced Example: Document Processing Pipeline")
    log("=" * 60)
    
    log("\nChecking Ollama...")
    if not check_ollama():
        log("ERROR: Ollama not running! Start with: ollama serve")
        return
    log("Ollama connected!")
    
    log("\n" + "-" * 60)
    log("Starting pipeline...")
    log("-" * 60)
    
    # Create and run the pipeline
    pipeline = create_pipeline()
    
    # Run with default sample document
    initial_state = PipelineState()
    
    result = pipeline.invoke(initial_state)
    
    # Display results
    log("\n" + "=" * 60)
    log("PIPELINE COMPLETE")
    log("=" * 60)
    
    final = result.get("final_output", {})
    summary = final.get("summary", {})
    
    log(f"\nDocument: {summary.get('document_title', 'N/A')}")
    log(f"Sections analyzed: {summary.get('total_sections', 0)}")
    log(f"Subsections: {summary.get('total_subsections', 0)}")
    log(f"Requirements found: {summary.get('total_requirements', 0)}")
    log(f"LLM analyses: {summary.get('analyses_performed', 0)}")
    
    log("\n" + "-" * 60)
    log("Processing Log:")
    log("-" * 60)
    for entry in result.get("processing_log", []):
        log(f"  • {entry}")
    
    log("\n" + "-" * 60)
    log("LLM Analysis Results:")
    log("-" * 60)
    for analysis in final.get("detailed_analysis", [])[:3]:
        log(f"\n  Section: {analysis.get('section')}")
        log(f"  Type: {analysis.get('analysis_type')}")
        result_preview = str(analysis.get('result', {}))[:200]
        log(f"  Result: {result_preview}...")
    
    # Save output to file
    output_file = "pipeline_output.json"
    with open(output_file, "w") as f:
        json.dump(final, f, indent=2)
    log(f"\n\nFull output saved to: {output_file}")
    
    log("\n" + "=" * 60)
    log("Pipeline execution complete!")
    log("=" * 60)


if __name__ == "__main__":
    main()

