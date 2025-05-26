import json
from typing import Dict, Any, Optional
from agents import function_tool, RunContextWrapper

@function_tool
async def process_chunk_content(ctx: RunContextWrapper[Any], chunk_content: str, document_type: str, chunk_id: str) -> str:
    """
    Process a chunk of document content and extract structured legal information.
    This is where the LLM will analyze the content and extract structured data.
    
    Args:
        chunk_content: The raw text content of the chunk
        document_type: Type of document (UU, Perpres, etc.)
        chunk_id: Identifier for this chunk
    
    Returns:
        JSON string containing structured legal document representation
    """
    # This function will be called by the LLM to process content
    # The LLM should analyze the chunk_content and return a structured representation
    
    # For now, return a basic structure - the LLM will fill this in intelligently
    basic_structure = {
        "metadata": {
            "title": "",
            "document_type": document_type,
            "number": "",
            "year": "",
            "subject": "",
            "issuing_authority": "",
            "source_file": ""
        },
        "preamble": None,
        "body": [],
        "closing": None,
        "explanation": None
    }
    
    return json.dumps(basic_structure, indent=2)

@function_tool
async def merge_chunk_results(ctx: RunContextWrapper[Any], document_id: str, processed_chunks_json: str) -> str:
    """
    Merge multiple processed chunks into a single coherent document structure.
    
    Args:
        document_id: Document identifier
        processed_chunks_json: JSON string containing list of processed chunk data
    
    Returns:
        JSON string containing merged document structure
    """
    try:
        processed_chunks = json.loads(processed_chunks_json)
        
        # Initialize the merged structure
        merged_metadata = None
        merged_preamble = None
        merged_body = []
        merged_closing = None
        merged_explanation = None
        
        # TODO: Handle cases where metadata/preamble/closing/explanation exists in multiple chunks
        for chunk_data in processed_chunks:
            if isinstance(chunk_data, dict):
                extracted = chunk_data.get("extracted_structure")
            else:
                extracted = chunk_data
            
            if not extracted:
                continue
                
            # Handle metadata - use the first complete one we find
            if not merged_metadata and extracted.get("metadata"):
                merged_metadata = extracted["metadata"]
            
            # Handle preamble - merge or use first one
            if not merged_preamble and extracted.get("preamble"):
                merged_preamble = extracted["preamble"]
            
            # Handle body sections - append all
            if extracted.get("body"):
                if isinstance(extracted["body"], list):
                    merged_body.extend(extracted["body"])
                else:
                    merged_body.append(extracted["body"])
            
            # Handle closing - use the last one we find
            if extracted.get("closing"):
                merged_closing = extracted["closing"]
            
            # Handle explanation - merge or use first one
            if not merged_explanation and extracted.get("explanation"):
                merged_explanation = extracted["explanation"]
        
        # Create default metadata if none found
        if not merged_metadata:
            merged_metadata = {
                "title": "Merged Document",
                "document_type": "unknown",
                "number": "",
                "year": "",
                "subject": "",
                "issuing_authority": "",
                "source_file": ""
            }
        
        merged_structure = {
            "metadata": merged_metadata,
            "preamble": merged_preamble,
            "body": merged_body,
            "closing": merged_closing,
            "explanation": merged_explanation
        }
        
        return json.dumps(merged_structure, indent=2)
        
    except Exception as e:
        error_structure = {
            "error": f"Error merging chunks: {str(e)}",
            "metadata": {
                "title": "Error Document",
                "document_type": "unknown",
                "number": "",
                "year": "",
                "subject": "",
                "issuing_authority": "",
                "source_file": ""
            },
            "preamble": None,
            "body": [],
            "closing": None,
            "explanation": None
        }
        return json.dumps(error_structure, indent=2)

@function_tool
async def validate_document_structure(ctx: RunContextWrapper[Any], structure_json: str) -> str:
    """
    Validate a document structure for completeness and consistency.
    
    Args:
        structure_json: JSON string containing the document structure to validate
    
    Returns:
        JSON string containing validation results
    """
    try:
        structure = json.loads(structure_json)
        
        validation_results = {
            "is_valid": True,
            "warnings": [],
            "errors": [],
            "suggestions": []
        }
        
        # Check metadata completeness
        metadata = structure.get("metadata", {})
        if not metadata.get("title"):
            validation_results["warnings"].append("Document title is missing")
        if not metadata.get("number"):
            validation_results["warnings"].append("Document number is missing")
        if not metadata.get("year"):
            validation_results["warnings"].append("Document year is missing")
        
        # Check body structure
        body = structure.get("body", [])
        if not body:
            validation_results["errors"].append("Document body is empty")
            validation_results["is_valid"] = False
        
        # Check for common legal document sections
        has_numbered_sections = any(
            section.get("type") in ["pasal", "bab", "bagian"] 
            for section in body 
            if isinstance(section, dict)
        )
        
        if not has_numbered_sections:
            validation_results["suggestions"].append("Consider organizing content into numbered sections (Pasal, Bab, etc.)")
        
        # Check for preamble in legal documents
        document_type = metadata.get("document_type", "")
        if document_type in ["UU", "Perpres", "PP"] and not structure.get("preamble"):
            validation_results["warnings"].append("Legal documents typically have a preamble section")
        
        return json.dumps(validation_results, indent=2)
        
    except Exception as e:
        error_result = {
            "is_valid": False,
            "warnings": [],
            "errors": [f"Error validating structure: {str(e)}"],
            "suggestions": []
        }
        return json.dumps(error_result, indent=2)

@function_tool
async def extract_document_metadata(ctx: RunContextWrapper[Any], content: str) -> str:
    """
    Extract metadata from document content using pattern matching and LLM analysis.
    
    Args:
        content: Raw document content
    
    Returns:
        JSON string containing document metadata
    """
    try:
        import re
        
        # Try to extract basic information using patterns
        title = ""
        doc_type = "unknown"
        number = ""
        year = ""
        subject = ""
        authority = ""
        
        content_upper = content.upper()
        
        # Extract document type and number
        uu_match = re.search(r'UNDANG-UNDANG.*?NOMOR\s+(\d+)\s+TAHUN\s+(\d+)', content_upper)
        if uu_match:
            doc_type = "UU"
            number = uu_match.group(1)
            year = uu_match.group(2)
        
        perpres_match = re.search(r'PERATURAN PRESIDEN.*?NOMOR\s+(\d+)\s+TAHUN\s+(\d+)', content_upper)
        if perpres_match:
            doc_type = "Perpres"
            number = perpres_match.group(1)
            year = perpres_match.group(2)
        
        # Extract subject (usually after "TENTANG")
        subject_match = re.search(r'TENTANG\s+(.*?)(?:\n|PRESIDEN|MENTERI)', content_upper)
        if subject_match:
            subject = subject_match.group(1).strip()
        
        # Extract authority
        if "PRESIDEN REPUBLIK INDONESIA" in content_upper:
            authority = "Presiden Republik Indonesia"
        elif "MENTERI" in content_upper:
            authority = "Menteri"
        
        # Create title
        if doc_type != "unknown" and number and year:
            title = f"{doc_type} Nomor {number} Tahun {year}"
            if subject:
                title += f" tentang {subject.title()}"
        
        metadata = {
            "title": title,
            "document_type": doc_type,
            "number": number,
            "year": year,
            "subject": subject.title() if subject else "",
            "issuing_authority": authority,
            "source_file": ""
        }
        
        return json.dumps(metadata, indent=2)
        
    except Exception as e:
        error_metadata = {
            "title": "",
            "document_type": "unknown",
            "number": "",
            "year": "",
            "subject": "",
            "issuing_authority": "",
            "source_file": "",
            "error": str(e)
        }
        return json.dumps(error_metadata, indent=2)
