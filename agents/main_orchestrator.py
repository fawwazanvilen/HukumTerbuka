#!/usr/bin/env python3
"""
Main Orchestrator Agent for HukumTerbuka
Coordinates the document processing workflow using OpenAI Agents SDK
"""

import asyncio
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime

from openai_agents import Agent, Runner, function_tool, RunContextWrapper
from pydantic import BaseModel

@dataclass
class DocumentContext:
    """Context for document processing"""
    document_id: str
    document_path: str
    chunks: List[str]
    processed_chunks: List[Dict[str, Any]]
    total_cost: float = 0.0
    start_time: Optional[datetime] = None

class ChunkResult(BaseModel):
    """Result from processing a chunk"""
    chunk_index: int
    content: str
    structured_data: Dict[str, Any]
    processing_cost: float

class MainOrchestrator:
    """Main orchestrator for the document processing workflow"""
    
    def __init__(self):
        self.context: Optional[DocumentContext] = None
        
        # Create the main orchestrator agent
        self.orchestrator_agent = Agent[DocumentContext](
            name="Document Processing Orchestrator",
            instructions="""
            You are the main orchestrator for processing Indonesian legal documents (UU).
            Your job is to:
            1. Analyze the document structure
            2. Create a processing plan
            3. Coordinate chunk-by-chunk processing
            4. Compile final results
            
            You work with specialized agents to process different parts of the document.
            Always maintain context awareness and track processing costs.
            """,
            tools=[self.naive_chunk_document, self.get_processing_status]
        )
    
    @function_tool
    async def naive_chunk_document(self, ctx: RunContextWrapper[DocumentContext], 
                                 document_text: str, chunk_size: int = 500) -> str:
        """
        Split document into naive chunks for processing
        
        Args:
            document_text: The full document text
            chunk_size: Size of each chunk in characters
        """
        chunks = []
        for i in range(0, len(document_text), chunk_size):
            chunk = document_text[i:i + chunk_size]
            chunks.append(chunk)
        
        # Update context
        ctx.context.chunks = chunks
        
        return f"Document split into {len(chunks)} chunks of ~{chunk_size} characters each"
    
    @function_tool
    async def get_processing_status(self, ctx: RunContextWrapper[DocumentContext]) -> str:
        """Get current processing status"""
        if not ctx.context:
            return "No document being processed"
        
        total_chunks = len(ctx.context.chunks)
        processed_chunks = len(ctx.context.processed_chunks)
        
        status = {
            "document_id": ctx.context.document_id,
            "total_chunks": total_chunks,
            "processed_chunks": processed_chunks,
            "progress": f"{processed_chunks}/{total_chunks}",
            "total_cost": ctx.context.total_cost
        }
        
        return json.dumps(status, indent=2)
    
    async def process_document(self, document_path: str) -> Dict[str, Any]:
        """Process a document using the multi-agent workflow"""
        
        # Initialize context
        document_id = Path(document_path).stem
        self.context = DocumentContext(
            document_id=document_id,
            document_path=document_path,
            chunks=[],
            processed_chunks=[],
            start_time=datetime.now()
        )
        
        # Read document
        with open(document_path, 'r', encoding='utf-8') as f:
            document_text = f.read()
        
        print(f"🚀 Starting document processing for {document_id}")
        print(f"📄 Document length: {len(document_text)} characters")
        
        # Run the orchestrator agent
        result = await Runner.run(
            self.orchestrator_agent,
            f"Process this Indonesian legal document:\n\n{document_text[:1000]}...\n\nFull document length: {len(document_text)} characters",
            context=self.context
        )
        
        print(f"🎯 Orchestrator result: {result.final_output}")
        
        return {
            "document_id": document_id,
            "orchestrator_output": result.final_output,
            "chunks_created": len(self.context.chunks),
            "processing_time": (datetime.now() - self.context.start_time).total_seconds()
        }

# Test function
async def test_orchestrator():
    """Test the main orchestrator"""
    orchestrator = MainOrchestrator()
    result = await orchestrator.process_document("raw/UU_8_1961.txt")
    
    print("\n📊 Processing Result:")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    return result

if __name__ == "__main__":
    asyncio.run(test_orchestrator())
