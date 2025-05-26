from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Union
from datetime import datetime

class DocumentMetadata(BaseModel):
    """Metadata for legal documents"""
    title: str
    document_type: str  # "UU", "Perpres", "Permen", etc.
    number: str
    year: str
    subject: str
    date_issued: Optional[str] = None
    issuing_authority: str
    source_file: str

class DocumentSection(BaseModel):
    """Generic section that can represent Bab, Pasal, Ayat, etc."""
    type: str  # "bab", "pasal", "ayat", "huruf", etc.
    number: str
    title: Optional[str] = None
    content: Optional[str] = None
    subsections: List["DocumentSection"] = Field(default_factory=list)
    
    class Config:
        # Allow self-referencing for nested structure
        arbitrary_types_allowed = True

# Update forward reference
DocumentSection.model_rebuild()

class LegalDocumentStructure(BaseModel):
    """Complete structure for any Indonesian legal document"""
    metadata: DocumentMetadata
    preamble: Optional[Dict[str, Any]] = None  # Pembukaan/Menimbang/Mengingat
    body: List[DocumentSection] = Field(default_factory=list)  # Main content
    closing: Optional[Dict[str, Any]] = None  # Penutup
    explanation: Optional[Dict[str, Any]] = None  # Penjelasan
    
class ChunkMetadata(BaseModel):
    """Metadata for document chunks"""
    chunk_id: str
    document_id: str
    chunk_type: str  # "page", "section", "paragraph"
    start_position: int
    end_position: int
    content_preview: str
    processing_status: str = "pending"  # "pending", "processing", "completed", "error"

class ProcessedChunk(BaseModel):
    """Result of processing a single chunk"""
    metadata: ChunkMetadata
    extracted_structure: Optional[LegalDocumentStructure] = None
    raw_content: str
    processing_notes: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)

class DocumentAnalysis(BaseModel):
    """Analysis result for document preprocessing"""
    document_type: str
    estimated_sections: int
    recommended_chunking_strategy: str
    complexity_score: float  # 0-1, higher = more complex
    structure_hints: List[str]
    total_length: int
