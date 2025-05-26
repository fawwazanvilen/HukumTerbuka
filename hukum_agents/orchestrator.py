import os
from typing import Any
from openai import AsyncOpenAI
from agents import Agent, Runner, set_default_openai_client, set_default_openai_api, set_tracing_disabled, set_trace_processors
import weave
from weave.integrations.openai_agents.openai_agents import WeaveTracingProcessor
from hukum_agents.tools import (
    analyze_document, chunk_document, extract_chunk_content,
    create_workspace, store_chunk_metadata, store_processed_chunk,
    query_workspace_status, get_processed_chunks, store_final_structure,
    process_chunk_content, merge_chunk_results, validate_document_structure,
    extract_document_metadata
)
from hukum_agents.models import ProcessedChunk, ChunkMetadata

# Set up custom client
custom_client = AsyncOpenAI(
    base_url="https://openrouter.ai/api/v1" or os.getenv("OPENAI_API_BASE_URL"),
    api_key=os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY")
)
set_default_openai_client(client=custom_client, use_for_tracing=True)
set_default_openai_api("chat_completions")
# set_tracing_disabled(disabled=True)
weave.init("openai-agents")
set_trace_processors([WeaveTracingProcessor()])

# Create the main orchestrator agent
orchestrator_agent = Agent(
    name="Legal Document Orchestrator",
    instructions="""
You are an intelligent legal document processing orchestrator for Indonesian legal documents. 
Your job is to coordinate the entire pipeline of converting legal documents (UU, Perpres, Permen, etc.) 
into structured JSON representations.

## Your Capabilities:
You have access to tools for:
1. Document analysis and chunking
2. Content processing and structure extraction  
3. File storage and workspace management
4. Result merging and validation

## Your Process:
1. **Analyze** the input document to understand its type, complexity, and optimal processing strategy
2. **Create workspace** for organizing the processing pipeline
3. **Chunk** the document based on your analysis (word count, character count, or paragraph grouping)
4. **Process each chunk** to extract structured legal information
5. **Store results** and track progress
6. **Merge chunks** into a coherent final structure
7. **Validate** the final result for completeness

## Key Principles:
- Make intelligent decisions about chunking strategy based on document characteristics
- Extract structured data that captures the hierarchical nature of legal documents (Bab → Pasal → Ayat)
- Handle various Indonesian legal document types (UU, Perpres, Permen, PP, Keppres)
- Maintain context across chunks to ensure coherent final structure
- Ask for human help when uncertain about complex legal structures
- Be flexible and adaptive - legal documents can have unexpected structures

## Output Format:
Always aim to produce structured JSON that includes:
- Metadata (title, type, number, year, subject, authority)
- Preamble (Menimbang, Mengingat, Memutuskan sections)
- Body (main content organized hierarchically)
- Closing (signatures, dates)
- Explanation (Penjelasan section if present)

## Decision Making:
You should intelligently decide:
- Optimal chunking strategy based on document length and complexity
- When to process chunks sequentially vs in parallel
- How to handle overlapping or incomplete information across chunks
- When to ask for human guidance on ambiguous legal structures
- How to merge and validate the final structure

Be thorough, intelligent, and adaptive in your approach. The goal is to create high-quality structured representations of Indonesian legal documents.
""",
    tools=[
        # Document analysis tools
        analyze_document,
        chunk_document, 
        extract_chunk_content,
        
        # Storage tools
        create_workspace,
        store_chunk_metadata,
        store_processed_chunk,
        query_workspace_status,
        get_processed_chunks,
        store_final_structure,
        
        # Processing tools
        process_chunk_content,
        merge_chunk_results,
        validate_document_structure,
        extract_document_metadata
    ],
    model="openai/gpt-4.1-mini"
)

async def process_legal_document(file_path: str, document_id: str = None) -> dict:
    """
    Main entry point for processing a legal document.
    
    Args:
        file_path: Path to the document file (PDF or TXT)
        document_id: Optional document identifier (will be generated if not provided)
    
    Returns:
        Dictionary containing the processing results
    """
    try:
        # Generate document ID if not provided
        if not document_id:
            import hashlib
            import time
            document_id = f"doc_{hashlib.md5(f"{file_path}_{time.time()}".encode()).hexdigest()[:8]}"

        # Create a simple context (can be expanded later)
        context = {"document_id": document_id, "file_path": file_path}
        
        # Start the orchestration process
        result = await Runner.run(
            orchestrator_agent,
            f"Process the legal document at: {file_path}. Document ID: {document_id}",
            context=context
        )
        
        return {
            "success": True,
            "document_id": document_id,
            "result": result.final_output,
            "workspace_path": f"output/documents/{document_id}"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "document_id": document_id
        }

# Convenience function for quick testing
async def quick_process(file_path: str = "raw/UU_8_1961.txt"):
    """Quick function to test the orchestrator with the sample document."""
    return await process_legal_document(file_path)
