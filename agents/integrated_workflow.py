#!/usr/bin/env python3
"""
Integrated Multi-Agent Workflow for HukumTerbuka
Combines the main orchestrator and chunk processor agents
"""

import asyncio
import json
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime

from agents.main_orchestrator import MainOrchestrator, DocumentContext
from agents.chunk_processor import ChunkProcessor, StructuredChunk

class IntegratedWorkflow:
    """Integrated workflow combining orchestrator and chunk processor"""
    
    def __init__(self):
        self.orchestrator = MainOrchestrator()
        self.chunk_processor = ChunkProcessor()
    
    async def process_document_with_chunks(self, document_path: str, chunk_size: int = 500) -> Dict[str, Any]:
        """
        Process a document using the integrated multi-agent workflow
        
        Args:
            document_path: Path to the document to process
            chunk_size: Size of each chunk in characters
        """
        
        print(f"🚀 Starting integrated workflow for {document_path}")
        
        # Step 1: Read the document
        with open(document_path, 'r', encoding='utf-8') as f:
            document_text = f.read()
        
        document_id = Path(document_path).stem
        start_time = datetime.now()
        
        print(f"📄 Document: {document_id} ({len(document_text)} characters)")
        
        # Step 2: Create naive chunks
        chunks = []
        for i in range(0, len(document_text), chunk_size):
            chunk = document_text[i:i + chunk_size]
            chunks.append(chunk)
        
        print(f"📦 Created {len(chunks)} chunks of ~{chunk_size} characters each")
        
        # Step 3: Process each chunk
        processed_chunks = []
        total_cost = 0.0
        
        for i, chunk_text in enumerate(chunks):
            print(f"\n🔄 Processing chunk {i+1}/{len(chunks)}")
            
            try:
                # Process chunk with context from previous chunks
                structured_chunk = await self.chunk_processor.process_chunk(
                    chunk_text=chunk_text,
                    chunk_index=i,
                    document_id=document_id,
                    previous_chunks=processed_chunks
                )
                
                processed_chunks.append(structured_chunk)
                
                # Simulate cost tracking (in real implementation, this would come from API calls)
                chunk_cost = len(chunk_text) * 0.00001  # Rough estimate
                total_cost += chunk_cost
                
                print(f"✅ Chunk {i+1} processed (cost: ${chunk_cost:.4f})")
                
            except Exception as e:
                print(f"❌ Error processing chunk {i+1}: {e}")
                # Create error chunk
                error_chunk = StructuredChunk(
                    chunk_index=i,
                    original_text=chunk_text,
                    section_type="error",
                    structured_content={"error": str(e)},
                    legal_elements=[],
                    cross_references=[]
                )
                processed_chunks.append(error_chunk)
        
        # Step 4: Compile final results
        processing_time = (datetime.now() - start_time).total_seconds()
        
        final_result = {
            "metadata": {
                "document_id": document_id,
                "document_path": document_path,
                "processing_started": start_time.isoformat(),
                "processing_completed": datetime.now().isoformat(),
                "processing_time_seconds": processing_time,
                "total_cost": total_cost,
                "chunk_size": chunk_size,
                "total_chunks": len(chunks),
                "successful_chunks": len([c for c in processed_chunks if c.section_type != "error"]),
                "error_chunks": len([c for c in processed_chunks if c.section_type == "error"])
            },
            "chunks": [chunk.model_dump() for chunk in processed_chunks],
            "summary": {
                "legal_elements_found": self._extract_all_legal_elements(processed_chunks),
                "cross_references_found": self._extract_all_cross_references(processed_chunks),
                "section_types_identified": list(set([c.section_type for c in processed_chunks if c.section_type]))
            }
        }
        
        print(f"\n🎉 Processing completed!")
        print(f"⏱️  Time: {processing_time:.2f} seconds")
        print(f"💰 Cost: ${total_cost:.4f}")
        print(f"📊 Success rate: {final_result['metadata']['successful_chunks']}/{final_result['metadata']['total_chunks']}")
        
        return final_result
    
    def _extract_all_legal_elements(self, chunks: List[StructuredChunk]) -> List[str]:
        """Extract all legal elements found across chunks"""
        all_elements = []
        for chunk in chunks:
            all_elements.extend(chunk.legal_elements)
        return list(set(all_elements))  # Remove duplicates
    
    def _extract_all_cross_references(self, chunks: List[StructuredChunk]) -> List[str]:
        """Extract all cross-references found across chunks"""
        all_refs = []
        for chunk in chunks:
            all_refs.extend(chunk.cross_references)
        return list(set(all_refs))  # Remove duplicates

# Test function
async def test_integrated_workflow():
    """Test the integrated workflow"""
    
    workflow = IntegratedWorkflow()
    
    # Process the UU document with small chunks for testing
    result = await workflow.process_document_with_chunks(
        document_path="raw/UU_8_1961.txt",
        chunk_size=300  # Small chunks for testing
    )
    
    # Save results
    output_path = "output/integrated_workflow_result.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Results saved to: {output_path}")
    
    # Print summary
    print("\n📊 Processing Summary:")
    print(f"  Document: {result['metadata']['document_id']}")
    print(f"  Chunks: {result['metadata']['total_chunks']}")
    print(f"  Success: {result['metadata']['successful_chunks']}")
    print(f"  Errors: {result['metadata']['error_chunks']}")
    print(f"  Time: {result['metadata']['processing_time_seconds']:.2f}s")
    print(f"  Cost: ${result['metadata']['total_cost']:.4f}")
    
    print(f"\n🔍 Legal Elements Found: {len(result['summary']['legal_elements_found'])}")
    for element in result['summary']['legal_elements_found'][:5]:  # Show first 5
        print(f"  - {element}")
    
    print(f"\n🔗 Cross-References Found: {len(result['summary']['cross_references_found'])}")
    for ref in result['summary']['cross_references_found'][:5]:  # Show first 5
        print(f"  - {ref}")
    
    return result

if __name__ == "__main__":
    asyncio.run(test_integrated_workflow())
