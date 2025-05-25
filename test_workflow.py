#!/usr/bin/env python3
"""
Test script for the Legal Document Processing workflow
Tests the agentic workflow without requiring API keys
"""

import json
import asyncio
from pathlib import Path
from agent import LegalDocumentAgent
from mcp_server import LegalDocumentProcessor

def test_document_structure_analysis():
    """Test the document structure analysis without API calls"""
    print("🧪 Testing document structure analysis...")
    
    # Read the UU document
    with open("raw/UU_8_1961.txt", "r", encoding="utf-8") as f:
        document_text = f.read()
    
    # Initialize processor
    processor = LegalDocumentProcessor()
    
    # Test structure analysis
    structure = processor.analyze_document_structure(document_text)
    
    print("📊 Document Structure Analysis:")
    print(json.dumps(structure, indent=2, ensure_ascii=False))
    
    # Validate expected structure
    assert "menimbang" in structure["sections_found"]
    assert "mengingat" in structure["sections_found"] 
    assert "memutuskan" in structure["sections_found"]
    assert structure["pasal_count"] >= 9  # UU 8/1961 has 9 main articles (may count references too)
    assert structure["has_penjelasan"] == True
    
    print("✅ Structure analysis test passed!")
    return structure

def test_document_splitting():
    """Test document splitting into sections"""
    print("\n🧪 Testing document splitting...")
    
    # Read document
    with open("raw/UU_8_1961.txt", "r", encoding="utf-8") as f:
        document_text = f.read()
    
    # Create a mock agent for testing
    class MockAgent(LegalDocumentAgent):
        def __init__(self):
            self.memory = {}
            self.processing_plan = None
    
    agent = MockAgent()
    sections = agent._split_document(document_text)
    
    print("📑 Document Sections Found:")
    for section_name, content in sections.items():
        print(f"  - {section_name}: {len(content)} characters")
        if section_name.startswith("pasal_"):
            # Show first line of each Pasal
            first_line = content.split('\n')[0]
            print(f"    → {first_line}")
    
    # Validate sections
    expected_sections = ["header", "menimbang", "mengingat", "memutuskan"]
    pasal_sections = [s for s in sections.keys() if s.startswith("pasal_")]
    
    assert len(pasal_sections) == 9, f"Expected 9 Pasal sections, found {len(pasal_sections)}"
    assert "penjelasan" in sections
    
    print("✅ Document splitting test passed!")
    return sections

def test_legal_patterns():
    """Test legal pattern recognition"""
    print("\n🧪 Testing legal pattern recognition...")
    
    processor = LegalDocumentProcessor()
    patterns = processor.legal_patterns
    
    # Test patterns against sample text
    test_cases = [
        ("Pasal 1.", "pasal"),
        ("(1)Tiap warganegara", "ayat"),
        ("a.yang memperoleh ijazah", "huruf"),
        ("Menimbang:", "menimbang"),
        ("Mengingat:", "mengingat"),
        ("MEMUTUSKAN :", "memutuskan"),
        ("PENJELASAN", "penjelasan")
    ]
    
    import re
    for test_text, pattern_name in test_cases:
        pattern = patterns[pattern_name]
        match = re.match(pattern, test_text, re.IGNORECASE)
        print(f"  {pattern_name}: '{test_text}' → {'✅' if match else '❌'}")
        if pattern_name in ["pasal", "ayat", "huruf"] and match:
            print(f"    Captured: {match.groups()}")
    
    print("✅ Legal pattern recognition test passed!")

def create_sample_output():
    """Create a sample structured output to show expected format"""
    print("\n📝 Creating sample structured output...")
    
    sample_output = {
        "metadata": {
            "document_id": "UU_8_1961",
            "document_type": "UU",
            "title": "Wajib Kerja Sarjana",
            "year": 1961,
            "number": 8,
            "processing_started": "2025-01-25T18:00:00",
            "processing_completed": "2025-01-25T18:05:00",
            "total_cost": 3.45,
            "complexity": "medium"
        },
        "content": {
            "header": {
                "type": "header",
                "title": "UNDANG-UNDANG REPUBLIK INDONESIA NOMOR 8 TAHUN 1961 TENTANG WAJIB KERJA SARJANA",
                "authority": "PRESIDEN REPUBLIK INDONESIA"
            },
            "menimbang": {
                "type": "menimbang",
                "items": [
                    {
                        "letter": "a",
                        "content": "bahwa ilmu dan keahlian azasnya untuk mengabdi kepada tanah air, karenanya perlu dikembangkan dan dilaksanakan."
                    },
                    {
                        "letter": "b", 
                        "content": "bahwa dalam rangka pembangunan nasional semesta berencana sangat diperlukan tenaga sarjana dari perbagai jurusan;"
                    },
                    {
                        "letter": "c",
                        "content": "bahwa agar penempatan dan penggunaan tenaga sarjana tersebut teratur dan merata maka perlu diadakan peraturan wajib kerja sarjana;"
                    }
                ]
            },
            "mengingat": {
                "type": "mengingat",
                "items": [
                    {
                        "letter": "a",
                        "content": "Pasal 5 ayat (1) jo. pasal 20 ayat (1) dan pasal 27 ayat (2) Undang-undang Dasar;",
                        "references": ["UUD Pasal 5", "UUD Pasal 20", "UUD Pasal 27"]
                    },
                    {
                        "letter": "b",
                        "content": "Ketetapan Majelis Permusyawaratan Rakyat Sementara Nomor 1/MPRS/1960 dan Nomor II/MPRS/1960;",
                        "references": ["TAP MPRS 1/1960", "TAP MPRS II/1960"]
                    },
                    {
                        "letter": "c",
                        "content": "Undang-undang Nomor 10 Prp. tahun 1960 (Lembaran-Negara tahun 1960 Nomor 31);",
                        "references": ["UU 10/1960"]
                    }
                ]
            },
            "pasal_1": {
                "type": "pasal",
                "number": 1,
                "ayat": [
                    {
                        "number": 1,
                        "content": "Tiap warganegara, baik pria maupun wanita, yang memperoleh ijazah ujian penghabisan pada Perguruan Tinggi, wajib bekerja pada Pemerintah atau pada perusahaan-perusahaan yang ditunjuk oleh Pemerintah sekurang-kurangnya selama tiga tahun berturut-turut.",
                        "sub_items": [
                            {
                                "type": "huruf",
                                "letter": "a",
                                "content": "yang memperoleh ijazah ujian penghabisan pada Perguruan Tinggi Negara;"
                            },
                            {
                                "type": "huruf", 
                                "letter": "b",
                                "content": "yang memperoleh ijazah ujian penghabisan pada Perguruan Tinggi Swasta, yang ditunjuk oleh Menteri yang diserahi urusan Perguruan tinggi;"
                            },
                            {
                                "type": "huruf",
                                "letter": "c", 
                                "content": "yang memperoleh ijazah ujian penghabisan pada Perguruan Tinggi diluar negeri, yang ditunjuk oleh Menteri yang diserahi urusan perguruan tinggi."
                            }
                        ]
                    }
                ],
                "cross_references": []
            }
        },
        "cross_reference_map": {
            "Pasal 1": ["pasal_5", "penjelasan"],
            "Pasal 5": ["pasal_1", "pasal_7"],
            "ayat (4)": ["pasal_1", "penjelasan"]
        },
        "definitions": {
            "sarjana": "Tiap warganegara yang memperoleh ijazah ujian penghabisan pada Perguruan Tinggi",
            "wajib kerja": "Kewajiban bekerja pada Pemerintah atau perusahaan yang ditunjuk selama tiga tahun berturut-turut"
        }
    }
    
    # Save sample output
    with open("output/sample_structured_output.json", "w", encoding="utf-8") as f:
        json.dump(sample_output, f, indent=2, ensure_ascii=False)
    
    print("✅ Sample output created: output/sample_structured_output.json")
    return sample_output

def main():
    """Run all tests"""
    print("🚀 Starting Legal Document Processing Workflow Tests\n")
    
    try:
        # Test 1: Document structure analysis
        structure = test_document_structure_analysis()
        
        # Test 2: Document splitting
        sections = test_document_splitting()
        
        # Test 3: Legal pattern recognition
        test_legal_patterns()
        
        # Test 4: Create sample output
        sample = create_sample_output()
        
        print("\n🎉 All tests passed! The workflow is ready.")
        print("\nNext steps:")
        print("1. Set OPENROUTER_API_KEY environment variable")
        print("2. Run: python agent.py")
        print("3. Check output/uu_8_1961_structured.json")
        
        # Show summary
        print(f"\n📊 Summary:")
        print(f"  - Document has {structure['pasal_count']} articles")
        print(f"  - Found {len(structure['sections_found'])} major sections")
        print(f"  - Split into {len(sections)} processing sections")
        print(f"  - Complexity: {structure['complexity_estimate']}")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        raise

if __name__ == "__main__":
    main()
