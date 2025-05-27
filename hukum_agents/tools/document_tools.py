import os
import re
import json
from pathlib import Path
from typing import List, Dict, Any
from agents import function_tool, RunContextWrapper

@function_tool
async def analyze_document(ctx: RunContextWrapper[Any], file_path: str) -> str:
    """
    Analyze a legal document to determine its type, structure, and optimal processing strategy.
    
    Args:
        file_path: Path to the document file (PDF or TXT)
    
    Returns:
        JSON string containing document analysis
    """
    try:
        # Read the document content
        if file_path.endswith('.txt'):
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        else:
            # For PDF files, we'd need PDF processing here
            # For now, assume we have a TXT version
            txt_path = file_path.replace('.pdf', '.txt')
            if os.path.exists(txt_path):
                with open(txt_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            else:
                raise FileNotFoundError(f"No TXT version found for {file_path}")
        
        content_lower = content.lower()
        
        # Analyze document type (case insensitive)
        document_type = "unknown"
        if "undang-undang" in content_lower:
            document_type = "UU"
        elif "peraturan presiden" in content_lower:
            document_type = "Perpres"
        elif "peraturan menteri" in content_lower:
            document_type = "Permen"
        elif "peraturan pemerintah" in content_lower:
            document_type = "PP"
        elif "keputusan presiden" in content_lower:
            document_type = "Keppres"
        
        # Count structural elements (case insensitive, more careful patterns)
        pasal_count = len(re.findall(r'\bpasal\s+\d+', content_lower))
        bab_count = len(re.findall(r'\bbab\s+[ivx]+', content_lower))
        ayat_count = len(re.findall(r'\(\d+\)', content))  # Ayat usually in parentheses
        
        # Determine complexity based on length and structure
        word_count = len(content.split())
        complexity_score = min(1.0, (word_count / 10000) * 0.5 + (pasal_count / 50) * 0.3 + (bab_count / 20) * 0.2)
        
        # Recommend chunking strategy based on document characteristics
        # if word_count < 1000:
        #     chunking_strategy = "single_chunk"
        # elif word_count < 5000:
        #     chunking_strategy = "by_words_2000"
        # elif word_count < 15000:
        #     chunking_strategy = "by_words_3000"
        # else:
        #     chunking_strategy = "by_words_4000"

        # just use a single chunking strategy for now
        chunking_strategy = "by_chars_2000"
        
        # Extract structure hints (case insensitive)
        structure_hints = []
        if "menimbang" in content_lower:
            structure_hints.append("has_preamble_considerations")
        if "mengingat" in content_lower:
            structure_hints.append("has_preamble_references")
        if "memutuskan" in content_lower:
            structure_hints.append("has_decision_section")
        if "penjelasan" in content_lower:
            structure_hints.append("has_explanation_section")
        if pasal_count > 0:
            structure_hints.append(f"contains_{pasal_count}_pasal_mentions")
        if bab_count > 0:
            structure_hints.append(f"contains_{bab_count}_bab_mentions")
        if ayat_count > 0:
            structure_hints.append(f"contains_{ayat_count}_numbered_items")
        
        # Add document length hints
        if word_count > 10000:
            structure_hints.append("long_document")
        elif word_count < 2000:
            structure_hints.append("short_document")
        else:
            structure_hints.append("medium_document")
        
        analysis = {
            "document_type": document_type,
            "estimated_sections": max(pasal_count, bab_count, 1),
            "recommended_chunking_strategy": chunking_strategy,
            "complexity_score": complexity_score,
            "structure_hints": structure_hints,
            "total_length": len(content)
        }
        
        return json.dumps(analysis, indent=2)
        
    except Exception as e:
        # Return a basic analysis if something goes wrong
        error_analysis = {
            "document_type": "unknown",
            "estimated_sections": 1,
            "recommended_chunking_strategy": "single_chunk",
            "complexity_score": 0.5,
            "structure_hints": ["analysis_failed"],
            "total_length": 0,
            "error": str(e)
        }
        return json.dumps(error_analysis, indent=2)

@function_tool
async def chunk_document(ctx: RunContextWrapper[Any], file_path: str, strategy: str, document_id: str) -> str:
    """
    Chunk a document based on the specified strategy.
    
    Args:
        file_path: Path to the document file
        strategy: Chunking strategy ("single_chunk", "by_words_N", "by_chars_N", "by_paragraphs_N")
        document_id: Unique identifier for this document
    
    Returns:
        JSON string containing list of chunk metadata
    """
    try:
        # Read content
        if file_path.endswith('.txt'):
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        else:
            txt_path = file_path.replace('.pdf', '.txt')
            with open(txt_path, 'r', encoding='utf-8') as f:
                content = f.read()
        
        chunks = []
        
        if strategy == "single_chunk":
            chunks.append({
                "chunk_id": f"{document_id}_chunk_001",
                "document_id": document_id,
                "chunk_type": "full_document",
                "start_position": 0,
                "end_position": len(content),
                "content_preview": content[:200] + "..." if len(content) > 200 else content
            })
            
        elif strategy.startswith("by_words_"):
            # Extract word count from strategy name
            try:
                word_limit = int(strategy.split("_")[-1])
            except:
                word_limit = 3000  # Default fallback
            
            words = content.split()
            current_chunk = []
            current_pos = 0
            chunk_num = 1
            
            for word in words:
                current_chunk.append(word)
                
                if len(current_chunk) >= word_limit:
                    chunk_content = " ".join(current_chunk)
                    chunks.append({
                        "chunk_id": f"{document_id}_chunk_{chunk_num:03d}",
                        "document_id": document_id,
                        "chunk_type": "word_based",
                        "start_position": current_pos,
                        "end_position": current_pos + len(chunk_content),
                        "content_preview": chunk_content[:200] + "..." if len(chunk_content) > 200 else chunk_content
                    })
                    current_pos += len(chunk_content) + 1  # +1 for space
                    current_chunk = []
                    chunk_num += 1
            
            # Handle remaining words
            if current_chunk:
                chunk_content = " ".join(current_chunk)
                chunks.append({
                    "chunk_id": f"{document_id}_chunk_{chunk_num:03d}",
                    "document_id": document_id,
                    "chunk_type": "word_based",
                    "start_position": current_pos,
                    "end_position": current_pos + len(chunk_content),
                    "content_preview": chunk_content[:200] + "..." if len(chunk_content) > 200 else chunk_content
                })
                
        elif strategy.startswith("by_chars_"):
            # Extract character count from strategy name
            try:
                char_limit = int(strategy.split("_")[-1])
            except:
                char_limit = 10000  # Default fallback
            
            current_pos = 0
            chunk_num = 1
            
            while current_pos < len(content):
                end_pos = min(current_pos + char_limit, len(content))
                
                # Try to break at word boundary if possible
                if end_pos < len(content):
                    # Look for last space within reasonable distance
                    for i in range(min(100, char_limit // 10)):
                        if content[end_pos - i] == ' ':
                            end_pos = end_pos - i
                            break
                
                chunk_content = content[current_pos:end_pos]
                chunks.append({
                    "chunk_id": f"{document_id}_chunk_{chunk_num:03d}",
                    "document_id": document_id,
                    "chunk_type": "character_based",
                    "start_position": current_pos,
                    "end_position": end_pos,
                    "content_preview": chunk_content[:200] + "..." if len(chunk_content) > 200 else chunk_content
                })
                
                current_pos = end_pos
                chunk_num += 1
                
        elif strategy.startswith("by_paragraphs_"):
            # Group multiple paragraphs together for better context
            try:
                para_count = int(strategy.split("_")[-1])
            except:
                para_count = 3  # Default: group 3 paragraphs together
            
            paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
            current_pos = 0
            chunk_num = 1
            
            for i in range(0, len(paragraphs), para_count):
                chunk_paragraphs = paragraphs[i:i + para_count]
                chunk_content = '\n\n'.join(chunk_paragraphs)
                
                chunks.append({
                    "chunk_id": f"{document_id}_chunk_{chunk_num:03d}",
                    "document_id": document_id,
                    "chunk_type": "paragraph_group",
                    "start_position": current_pos,
                    "end_position": current_pos + len(chunk_content),
                    "content_preview": chunk_content[:200] + "..." if len(chunk_content) > 200 else chunk_content
                })
                
                current_pos += len(chunk_content) + 4  # +4 for \n\n\n\n between groups
                chunk_num += 1
        
        return json.dumps(chunks, indent=2)
        
    except Exception as e:
        # Return single chunk as fallback
        error_chunk = [{
            "chunk_id": f"{document_id}_chunk_001",
            "document_id": document_id,
            "chunk_type": "error_fallback",
            "start_position": 0,
            "end_position": 0,
            "content_preview": f"Error chunking document: {str(e)}"
        }]
        return json.dumps(error_chunk, indent=2)

@function_tool
async def extract_chunk_content(ctx: RunContextWrapper[Any], file_path: str, chunk_metadata_json: str) -> str:
    """
    Extract the actual content for a specific chunk.
    
    Args:
        file_path: Path to the source document
        chunk_metadata_json: JSON string containing chunk metadata
    """
    try:
        chunk_metadata = json.loads(chunk_metadata_json)
        
        # Read content
        if file_path.endswith('.txt'):
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        else:
            txt_path = file_path.replace('.pdf', '.txt')
            with open(txt_path, 'r', encoding='utf-8') as f:
                content = f.read()
        
        # Extract the specific chunk
        start = chunk_metadata.get("start_position", 0)
        end = chunk_metadata.get("end_position", len(content))
        
        return content[start:end]
        
    except Exception as e:
        return f"Error extracting chunk content: {str(e)}"
