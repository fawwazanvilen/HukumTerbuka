#!/usr/bin/env python3
"""
Test script for the basic multi-agent setup
Tests the orchestrator and chunk processor without requiring API keys
"""

import asyncio
import json
import os
from pathlib import Path

# Test without actual API calls first
def test_imports():
    """Test that all imports work correctly"""
    print("🧪 Testing imports...")
    
    try:
        from agents import MainOrchestrator, ChunkProcessor, IntegratedWorkflow
        from agents.chunk_processor import StructuredChunk
        print("✅ All imports successful")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def test_data_structures():
    """Test the data structures work correctly"""
    print("\n🧪 Testing data structures...")
    
    try:
        from agents.chunk_processor import StructuredChunk
        
        # Test creating a StructuredChunk
        chunk = StructuredChunk(
            chunk_index=0,
            original_text="Test chunk text",
            section_type="test",
            structured_content={"test": "data"},
            legal_elements=["pasal", "ayat"],
            cross_references=["ref_1", "ref_2"]
        )
        
        print(f"✅ StructuredChunk created: {chunk.chunk_index}")
        print(f"   Section type: {chunk.section_type}")
        print(f"   Legal elements: {chunk.legal_elements}")
        
        # Test serialization
        chunk_dict = chunk.model_dump()
        print(f"✅ Serialization works: {len(chunk_dict)} fields")
        
        return True
    except Exception as e:
        print(f"❌ Data structure error: {e}")
        return False

def test_document_reading():
    """Test reading the document file"""
    print("\n🧪 Testing document reading...")
    
    try:
        document_path = "raw/UU_8_1961.txt"
        if not Path(document_path).exists():
            print(f"❌ Document not found: {document_path}")
            return False
        
        with open(document_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        print(f"✅ Document read successfully: {len(content)} characters")
        
        # Test chunking logic
        chunk_size = 300
        chunks = []
        for i in range(0, len(content), chunk_size):
            chunk = content[i:i + chunk_size]
            chunks.append(chunk)
        
        print(f"✅ Chunking works: {len(chunks)} chunks of ~{chunk_size} chars")
        
        # Show first chunk preview
        if chunks:
            preview = chunks[0][:100] + "..." if len(chunks[0]) > 100 else chunks[0]
            print(f"   First chunk preview: {preview}")
        
        return True
    except Exception as e:
        print(f"❌ Document reading error: {e}")
        return False

def test_pattern_matching():
    """Test legal pattern matching without API calls"""
    print("\n🧪 Testing legal pattern matching...")
    
    try:
        import re
        
        # Sample text from Indonesian legal document
        sample_text = """
        Pasal 1
        (1) Tiap warganegara, baik pria maupun wanita, yang memperoleh ijazah
        a. yang memperoleh ijazah ujian penghabisan pada Perguruan Tinggi Negara;
        b. yang memperoleh ijazah ujian penghabisan pada Perguruan Tinggi Swasta;
        
        Menimbang:
        a. bahwa ilmu dan keahlian azasnya untuk mengabdi kepada tanah air;
        
        Mengingat:
        a. Pasal 5 ayat (1) jo. pasal 20 ayat (1) Undang-undang Dasar;
        """
        
        patterns = {
            'pasal': r'Pasal\s+(\d+)',
            'ayat': r'\((\d+)\)',
            'huruf': r'^([a-z])\.',
            'menimbang': r'Menimbang\s*:',
            'mengingat': r'Mengingat\s*:',
        }
        
        results = {}
        for pattern_name, pattern in patterns.items():
            matches = re.findall(pattern, sample_text, re.MULTILINE | re.IGNORECASE)
            results[pattern_name] = matches
            print(f"   {pattern_name}: {matches}")
        
        print("✅ Pattern matching works")
        return True
    except Exception as e:
        print(f"❌ Pattern matching error: {e}")
        return False

async def test_basic_workflow_structure():
    """Test the basic workflow structure without API calls"""
    print("\n🧪 Testing basic workflow structure...")
    
    try:
        from agents import IntegratedWorkflow
        
        # Create workflow instance
        workflow = IntegratedWorkflow()
        print("✅ IntegratedWorkflow instance created")
        
        # Test that we can access the components
        print(f"✅ Orchestrator available: {workflow.orchestrator is not None}")
        print(f"✅ Chunk processor available: {workflow.chunk_processor is not None}")
        
        return True
    except Exception as e:
        print(f"❌ Workflow structure error: {e}")
        return False

def create_mock_result():
    """Create a mock result to test output format"""
    print("\n🧪 Creating mock result...")
    
    try:
        from agents.chunk_processor import StructuredChunk
        from datetime import datetime
        
        # Create mock processed chunks
        mock_chunks = [
            StructuredChunk(
                chunk_index=0,
                original_text="UNDANG-UNDANG REPUBLIK INDONESIA NOMOR 8 TAHUN 1961",
                section_type="header",
                structured_content={"title": "UU 8/1961", "year": 1961},
                legal_elements=["title"],
                cross_references=[]
            ),
            StructuredChunk(
                chunk_index=1,
                original_text="Menimbang: a. bahwa ilmu dan keahlian...",
                section_type="menimbang",
                structured_content={"considerations": ["ilmu dan keahlian"]},
                legal_elements=["menimbang"],
                cross_references=[]
            ),
            StructuredChunk(
                chunk_index=2,
                original_text="Pasal 1 (1) Tiap warganegara...",
                section_type="pasal",
                structured_content={"pasal_number": 1, "ayat": [1]},
                legal_elements=["pasal: ['1']", "ayat: ['1']"],
                cross_references=["ref_1"]
            )
        ]
        
        # Create mock final result
        mock_result = {
            "metadata": {
                "document_id": "UU_8_1961",
                "processing_started": datetime.now().isoformat(),
                "processing_completed": datetime.now().isoformat(),
                "processing_time_seconds": 1.5,
                "total_cost": 0.0045,
                "chunk_size": 300,
                "total_chunks": 3,
                "successful_chunks": 3,
                "error_chunks": 0
            },
            "chunks": [chunk.model_dump() for chunk in mock_chunks],
            "summary": {
                "legal_elements_found": ["title", "menimbang", "pasal: ['1']", "ayat: ['1']"],
                "cross_references_found": ["ref_1"],
                "section_types_identified": ["header", "menimbang", "pasal"]
            }
        }
        
        # Save mock result
        output_path = "output/mock_workflow_result.json"
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(mock_result, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Mock result created: {output_path}")
        print(f"   Chunks: {len(mock_chunks)}")
        print(f"   Legal elements: {len(mock_result['summary']['legal_elements_found'])}")
        
        return True
    except Exception as e:
        print(f"❌ Mock result error: {e}")
        return False

async def main():
    """Run all basic tests"""
    print("🚀 Starting Basic Multi-Agent System Tests\n")
    
    tests = [
        ("Import Test", test_imports),
        ("Data Structures Test", test_data_structures),
        ("Document Reading Test", test_document_reading),
        ("Pattern Matching Test", test_pattern_matching),
        ("Workflow Structure Test", test_basic_workflow_structure),
        ("Mock Result Test", create_mock_result)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print(f"\n📊 Test Results Summary:")
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status} {test_name}")
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All basic tests passed! The multi-agent structure is ready.")
        print("\nNext steps:")
        print("1. Install dependencies: pip install -r requirements.txt")
        print("2. Set OPENAI_API_KEY environment variable")
        print("3. Test with actual API calls")
    else:
        print(f"\n⚠️  {total - passed} tests failed. Please fix issues before proceeding.")
    
    return passed == total

if __name__ == "__main__":
    asyncio.run(main())
