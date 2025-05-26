#!/usr/bin/env python3
"""
Chunk Processor Agent for HukumTerbuka
Processes individual chunks of legal documents into structured format
"""

import asyncio
import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

from openai_agents import Agent, Runner, function_tool, RunContextWrapper
from pydantic import BaseModel

class StructuredChunk(BaseModel):
    """Structured representation of a processed chunk"""
    chunk_index: int
    original_text: str
    section_type: Optional[str] = None
    structured_content: Dict[str, Any] = {}
    legal_elements: List[str] = []
    cross_references: List[str] = []

@dataclass
class ChunkContext:
    """Context for chunk processing"""
    document_id: str
    chunk_index: int
    previous_chunks: List[StructuredChunk]
    processing_cost: float = 0.0

class ChunkProcessor:
    """Agent specialized in processing individual document chunks"""
    
    def __init__(self):
        # Create the chunk processor agent
        self.processor_agent = Agent[ChunkContext](
            name="Legal Chunk Processor",
            instructions="""
            You are a specialized agent for processing chunks of Indonesian legal documents (UU).
            
            Your tasks:
            1. Analyze the chunk text to identify legal structure elements
            2. Extract structured information (Pasal, Ayat, Huruf, etc.)
            3. Identify cross-references to other parts of the document
            4. Maintain consistency with previously processed chunks
            
            Indonesian legal document structure:
            - Bab (Chapters)
            - Bagian (Sections) 
            - Pasal (Articles)
            - Ayat (Verses/Paragraphs)
            - Huruf (Lettered sub-items: a, b, c...)
            - Angka (Numbered sub-items: 1, 2, 3...)
            - Menimbang (Considerations)
            - Mengingat (References)
            - Memutuskan (Decisions)
            - Penjelasan (Explanations)
            
            Always provide structured output in JSON format.
            """,
            output_type=StructuredChunk,
            tools=[self.identify_legal_elements, self.extract_cross_references]
        )
    
    @function_tool
    async def identify_legal_elements(self, ctx: RunContextWrapper[ChunkContext], 
                                    text: str) -> str:
        """
        Identify legal structure elements in the text
        
        Args:
            text: The chunk text to analyze
        """
        elements = []
        
        # Simple pattern matching for legal elements
        import re
        
        patterns = {
            'pasal': r'Pasal\s+(\d+)',
            'ayat': r'\((\d+)\)',
            'huruf': r'^([a-z])\.',
            'angka': r'^(\d+)\.',
            'menimbang': r'Menimbang\s*:',
            'mengingat': r'Mengingat\s*:',
            'memutuskan': r'MEMUTUSKAN',
            'penjelasan': r'PENJELASAN'
        }
        
        for element_type, pattern in patterns.items():
            matches = re.findall(pattern, text, re.MULTILINE | re.IGNORECASE)
            if matches:
                elements.append(f"{element_type}: {matches}")
        
        return f"Legal elements found: {elements}"
    
    @function_tool
    async def extract_cross_references(self, ctx: RunContextWrapper[ChunkContext], 
                                     text: str) -> str:
        """
        Extract cross-references to other parts of the document
        
        Args:
            text: The chunk text to analyze
        """
        import re
        
        # Pattern for cross-references
        ref_patterns = [
            r'Pasal\s+(\d+)',
            r'ayat\s+\((\d+)\)',
            r'huruf\s+([a-z])',
            r'Undang-undang\s+Nomor\s+(\d+)',
            r'Peraturan\s+Pemerintah\s+Nomor\s+(\d+)'
        ]
        
        references = []
        for pattern in ref_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                references.extend([f"ref_{match}" for match in matches])
        
        return f"Cross-references found: {references}"
    
    async def process_chunk(self, chunk_text: str, chunk_index: int, 
                          document_id: str, previous_chunks: List[StructuredChunk] = None) -> StructuredChunk:
        """
        Process a single chunk of text
        
        Args:
            chunk_text: The text chunk to process
            chunk_index: Index of this chunk
            document_id: ID of the document being processed
            previous_chunks: Previously processed chunks for context
        """
        
        if previous_chunks is None:
            previous_chunks = []
        
        # Create context
        context = ChunkContext(
            document_id=document_id,
            chunk_index=chunk_index,
            previous_chunks=previous_chunks
        )
        
        print(f"🔄 Processing chunk {chunk_index} ({len(chunk_text)} chars)")
        
        # Create input for the agent
        input_text = f"""
        Process this chunk of Indonesian legal document:
        
        Document ID: {document_id}
        Chunk Index: {chunk_index}
        
        Chunk Text:
        {chunk_text}
        
        Previous chunks processed: {len(previous_chunks)}
        
        Please analyze this chunk and provide structured output.
        """
        
        try:
            # Run the processor agent
            result = await Runner.run(
                self.processor_agent,
                input_text,
                context=context
            )
            
            # The result should be a StructuredChunk due to output_type
            structured_chunk = result.final_output
            
            print(f"✅ Chunk {chunk_index} processed successfully")
            return structured_chunk
            
        except Exception as e:
            print(f"❌ Error processing chunk {chunk_index}: {e}")
            # Return a basic structured chunk on error
            return StructuredChunk(
                chunk_index=chunk_index,
                original_text=chunk_text,
                section_type="error",
                structured_content={"error": str(e)},
                legal_elements=[],
                cross_references=[]
            )

# Test function
async def test_chunk_processor():
    """Test the chunk processor with a sample chunk"""
    
    # Read a sample from the document
    with open("raw/UU_8_1961.txt", 'r', encoding='utf-8') as f:
        document_text = f.read()
    
    # Take first 500 characters as test chunk
    test_chunk = document_text[:500]
    
    processor = ChunkProcessor()
    result = await processor.process_chunk(
        chunk_text=test_chunk,
        chunk_index=0,
        document_id="UU_8_1961"
    )
    
    print("\n📊 Chunk Processing Result:")
    print(json.dumps(result.model_dump(), indent=2, ensure_ascii=False))
    
    return result

if __name__ == "__main__":
    asyncio.run(test_chunk_processor())
