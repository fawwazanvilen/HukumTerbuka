import os
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
from agents import function_tool, RunContextWrapper

@function_tool
async def create_workspace(ctx: RunContextWrapper[Any], document_id: str, source_file: str) -> str:
    """
    Create a workspace directory structure for processing a document.
    
    Args:
        document_id: Unique identifier for the document
        source_file: Path to the source document file
    """
    try:
        # Create the workspace directory structure
        workspace_path = Path("output") / "documents" / document_id
        workspace_path.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories
        (workspace_path / "chunks").mkdir(exist_ok=True)
        (workspace_path / "processed").mkdir(exist_ok=True)
        
        # Create metadata file
        metadata = {
            "document_id": document_id,
            "source_file": source_file,
            "created_at": datetime.now().isoformat(),
            "status": "initialized",
            "total_chunks": 0,
            "processed_chunks": 0
        }
        
        with open(workspace_path / "metadata.json", 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        return str(workspace_path)
        
    except Exception as e:
        return f"Error creating workspace: {str(e)}"

@function_tool
async def store_chunk_metadata(ctx: RunContextWrapper[Any], document_id: str, chunks_json: str) -> str:
    """
    Store chunk metadata in the workspace.
    
    Args:
        document_id: Document identifier
        chunks_json: JSON string containing list of chunk metadata
    """
    try:
        workspace_path = Path("output") / "documents" / document_id
        chunks_data = json.loads(chunks_json)
        
        # Store individual chunk metadata
        for chunk_data in chunks_data:
            chunk_id = chunk_data.get("chunk_id")
            chunk_file = workspace_path / "chunks" / f"{chunk_id}_metadata.json"
            with open(chunk_file, 'w', encoding='utf-8') as f:
                json.dump(chunk_data, f, indent=2, ensure_ascii=False)
        
        # Update workspace metadata
        metadata_file = workspace_path / "metadata.json"
        if metadata_file.exists():
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            
            metadata["total_chunks"] = len(chunks_data)
            metadata["chunks_created_at"] = datetime.now().isoformat()
            
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        return f"Stored metadata for {len(chunks_data)} chunks"
        
    except Exception as e:
        return f"Error storing chunk metadata: {str(e)}"

@function_tool
async def store_processed_chunk(ctx: RunContextWrapper[Any], document_id: str, processed_chunk_json: str) -> str:
    """
    Store a processed chunk result.
    
    Args:
        document_id: Document identifier
        processed_chunk_json: JSON string containing the processed chunk data
    """
    try:
        workspace_path = Path("output") / "documents" / document_id
        processed_chunk_data = json.loads(processed_chunk_json)
        
        chunk_id = processed_chunk_data.get("metadata", {}).get("chunk_id")
        if not chunk_id:
            return "Error: No chunk_id found in processed chunk data"
        
        # Store the processed chunk
        chunk_file = workspace_path / "processed" / f"{chunk_id}.json"
        with open(chunk_file, 'w', encoding='utf-8') as f:
            json.dump(processed_chunk_data, f, indent=2, ensure_ascii=False, default=str)
        
        # Update chunk metadata status
        metadata_file = workspace_path / "chunks" / f"{chunk_id}_metadata.json"
        if metadata_file.exists():
            with open(metadata_file, 'r', encoding='utf-8') as f:
                chunk_metadata = json.load(f)
            
            chunk_metadata["processing_status"] = "completed"
            chunk_metadata["processed_at"] = datetime.now().isoformat()
            
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(chunk_metadata, f, indent=2, ensure_ascii=False)
        
        # Update workspace metadata
        workspace_metadata_file = workspace_path / "metadata.json"
        if workspace_metadata_file.exists():
            with open(workspace_metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            
            metadata["processed_chunks"] = metadata.get("processed_chunks", 0) + 1
            metadata["last_processed_at"] = datetime.now().isoformat()
            
            with open(workspace_metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        return f"Stored processed chunk: {chunk_id}"
        
    except Exception as e:
        return f"Error storing processed chunk: {str(e)}"

@function_tool
async def query_workspace_status(ctx: RunContextWrapper[Any], document_id: str) -> str:
    """
    Query the current status of a document workspace.
    
    Args:
        document_id: Document identifier
    """
    try:
        workspace_path = Path("output") / "documents" / document_id
        
        if not workspace_path.exists():
            return json.dumps({"error": f"Workspace for {document_id} does not exist"})
        
        # Read workspace metadata
        metadata_file = workspace_path / "metadata.json"
        if metadata_file.exists():
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
        else:
            metadata = {}
        
        # Count actual files
        chunks_dir = workspace_path / "chunks"
        processed_dir = workspace_path / "processed"
        
        chunk_files = list(chunks_dir.glob("*_metadata.json")) if chunks_dir.exists() else []
        processed_files = list(processed_dir.glob("*.json")) if processed_dir.exists() else []
        
        # Get list of pending chunks
        pending_chunks = []
        completed_chunks = []
        
        for chunk_file in chunk_files:
            with open(chunk_file, 'r', encoding='utf-8') as f:
                chunk_data = json.load(f)
            
            if chunk_data.get("processing_status") == "completed":
                completed_chunks.append(chunk_data["chunk_id"])
            else:
                pending_chunks.append(chunk_data["chunk_id"])
        
        result = {
            "document_id": document_id,
            "workspace_path": str(workspace_path),
            "metadata": metadata,
            "total_chunks": len(chunk_files),
            "processed_chunks": len(processed_files),
            "pending_chunks": pending_chunks,
            "completed_chunks": completed_chunks,
            "progress_percentage": (len(processed_files) / len(chunk_files) * 100) if chunk_files else 0
        }
        
        return json.dumps(result, indent=2)
        
    except Exception as e:
        return json.dumps({"error": f"Error querying workspace: {str(e)}"})

@function_tool
async def get_processed_chunks(ctx: RunContextWrapper[Any], document_id: str, limit: int = 0) -> str:
    """
    Retrieve processed chunks for a document.
    
    Args:
        document_id: Document identifier
        limit: Maximum number of chunks to return (0 for all)
    """
    try:
        workspace_path = Path("output") / "documents" / document_id
        processed_dir = workspace_path / "processed"
        
        if not processed_dir.exists():
            return json.dumps([])
        
        processed_files = list(processed_dir.glob("*.json"))
        if limit > 0:
            processed_files = processed_files[:limit]
        
        chunks = []
        for file_path in processed_files:
            with open(file_path, 'r', encoding='utf-8') as f:
                chunk_data = json.load(f)
                chunks.append(chunk_data)
        
        # Sort by chunk_id for consistent ordering
        chunks.sort(key=lambda x: x.get("metadata", {}).get("chunk_id", ""))
        
        return json.dumps(chunks, indent=2)
        
    except Exception as e:
        return json.dumps([{"error": f"Error retrieving processed chunks: {str(e)}"}])

@function_tool
async def store_final_structure(ctx: RunContextWrapper[Any], document_id: str, final_structure_json: str) -> str:
    """
    Store the final merged document structure.
    
    Args:
        document_id: Document identifier
        final_structure_json: JSON string containing the complete document structure
    """
    try:
        workspace_path = Path("output") / "documents" / document_id
        final_structure_data = json.loads(final_structure_json)
        
        # Store the final structure
        final_file = workspace_path / "final_structure.json"
        with open(final_file, 'w', encoding='utf-8') as f:
            json.dump(final_structure_data, f, indent=2, ensure_ascii=False, default=str)
        
        # Update workspace metadata
        metadata_file = workspace_path / "metadata.json"
        if metadata_file.exists():
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            
            metadata["status"] = "completed"
            metadata["completed_at"] = datetime.now().isoformat()
            
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        return f"Stored final structure for document {document_id}"
        
    except Exception as e:
        return f"Error storing final structure: {str(e)}"

@function_tool
async def search_processed_content(ctx: RunContextWrapper[Any], document_id: str, search_term: str) -> str:
    """
    Search through processed chunks for specific content.
    
    Args:
        document_id: Document identifier
        search_term: Term to search for (case insensitive)
    """
    try:
        processed_chunks_json = await get_processed_chunks(ctx, document_id)
        processed_chunks = json.loads(processed_chunks_json)
        
        matching_chunks = []
        search_term_lower = search_term.lower()
        
        for chunk in processed_chunks:
            # Search in raw content
            raw_content = chunk.get("raw_content", "").lower()
            if search_term_lower in raw_content:
                matching_chunks.append({
                    "chunk_id": chunk.get("metadata", {}).get("chunk_id"),
                    "match_type": "raw_content",
                    "preview": chunk.get("raw_content", "")[:300] + "..."
                })
            
            # Search in extracted structure (if available)
            extracted = chunk.get("extracted_structure")
            if extracted:
                structure_str = json.dumps(extracted).lower()
                if search_term_lower in structure_str:
                    matching_chunks.append({
                        "chunk_id": chunk.get("metadata", {}).get("chunk_id"),
                        "match_type": "extracted_structure",
                        "preview": json.dumps(extracted, indent=2)[:300] + "..."
                    })
        
        return json.dumps(matching_chunks, indent=2)
        
    except Exception as e:
        return json.dumps([{"error": f"Error searching content: {str(e)}"}])
