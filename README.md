# HukumTerbuka - Legal Document Processing System

An intelligent agent orchestration system for processing Indonesian legal documents (UU, Perpres, Permen, etc.) into structured JSON representations using OpenAI's Agents SDK.

## 🎯 Project Overview

HukumTerbuka aims to create a "ground truth" structured representation of Indonesian legal documents that can serve as the foundation for downstream applications. The system uses an intelligent agent orchestration approach to:

1. **Analyze** legal documents to understand their structure and complexity
2. **Chunk** documents using optimal strategies (word count, character count, paragraph grouping)
3. **Process** each chunk to extract structured legal information
4. **Merge** results into a coherent final structure
5. **Validate** the output for completeness and consistency

## 🏗️ Architecture

The system follows a modular agent-based architecture:

```
HukumTerbuka/
├── hukum_agents/           # Main agent system
│   ├── models/            # Pydantic schemas
│   ├── tools/             # Agent tools
│   │   ├── document_tools.py    # Document analysis & chunking
│   │   ├── storage_tools.py     # File-based workspace management
│   │   └── processing_tools.py  # Content processing & merging
│   └── orchestrator.py    # Main orchestrator agent
├── raw/                   # Input documents
├── output/               # Processing workspaces
└── main.py              # Entry point
```

### Key Components

- **Orchestrator Agent**: Main intelligent coordinator that manages the entire pipeline
- **Document Tools**: Analyze document characteristics and create optimal chunking strategies
- **Storage Tools**: File-based workspace management for tracking progress and storing results
- **Processing Tools**: Extract structured data from chunks and merge results

## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- OpenAI API key

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd HukumTerbuka
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
```

### Usage

#### Basic Usage
```bash
python main.py
```

#### Interactive Mode
```bash
python main.py --interactive
```

#### Programmatic Usage
```python
import asyncio
from hukum_agents import process_legal_document

async def main():
    result = await process_legal_document("path/to/document.txt")
    if result["success"]:
        print(f"Workspace: {result['workspace_path']}")
        print(f"Result: {result['result']}")

asyncio.run(main())
```

## 📊 Data Models

The system uses structured Pydantic models to represent legal documents:

### DocumentMetadata
```python
{
    "title": "UU Nomor 8 Tahun 1961 tentang Wajib Kerja",
    "document_type": "UU",
    "number": "8", 
    "year": "1961",
    "subject": "Wajib Kerja",
    "issuing_authority": "Presiden Republik Indonesia",
    "source_file": "raw/UU_8_1961.txt"
}
```

### DocumentSection (Hierarchical)
```python
{
    "type": "pasal",
    "number": "1", 
    "title": "Definisi",
    "content": "Dalam Undang-undang ini yang dimaksud dengan...",
    "subsections": [
        {
            "type": "ayat",
            "number": "1",
            "content": "..."
        }
    ]
}
```

### LegalDocumentStructure
```python
{
    "metadata": DocumentMetadata,
    "preamble": {
        "menimbang": [...],
        "mengingat": [...],
        "memutuskan": [...]
    },
    "body": [DocumentSection],
    "closing": {...},
    "explanation": {...}
}
```

## 🔧 Chunking Strategies

The system supports flexible chunking strategies:

- **single_chunk**: Process entire document at once (for small documents)
- **by_words_N**: Chunk by word count (e.g., by_words_2000)
- **by_chars_N**: Chunk by character count (e.g., by_chars_10000)
- **by_paragraphs_N**: Group N paragraphs together (e.g., by_paragraphs_3)

The orchestrator agent intelligently selects the optimal strategy based on document characteristics.

## 📁 Workspace Structure

Each processed document gets its own workspace:

```
output/documents/{document_id}/
├── metadata.json              # Workspace metadata
├── chunks/                    # Chunk metadata
│   ├── {chunk_id}_metadata.json
│   └── ...
├── processed/                 # Processed chunk results
│   ├── {chunk_id}.json
│   └── ...
└── final_structure.json       # Final merged result
```

## 🛠️ Tools Available to Agents

### Document Analysis Tools
- `analyze_document`: Analyze document type, complexity, and recommend chunking strategy
- `chunk_document`: Split document using specified strategy
- `extract_chunk_content`: Extract content for specific chunks

### Storage Tools
- `create_workspace`: Set up processing workspace
- `store_chunk_metadata`: Store chunk information
- `store_processed_chunk`: Store processing results
- `query_workspace_status`: Check processing progress
- `get_processed_chunks`: Retrieve processed results
- `store_final_structure`: Save final merged structure

### Processing Tools
- `process_chunk_content`: Extract structured data from chunk content
- `merge_chunk_results`: Combine multiple chunk results
- `validate_document_structure`: Check result completeness
- `extract_document_metadata`: Extract document metadata

## 🎯 Supported Document Types

- **UU** (Undang-Undang) - Laws
- **Perpres** (Peraturan Presiden) - Presidential Regulations  
- **Permen** (Peraturan Menteri) - Ministerial Regulations
- **PP** (Peraturan Pemerintah) - Government Regulations
- **Keppres** (Keputusan Presiden) - Presidential Decisions

## 🔄 Processing Flow

1. **Document Analysis**: Analyze document type, length, and structure
2. **Workspace Creation**: Set up organized file structure for processing
3. **Intelligent Chunking**: Split document using optimal strategy
4. **Chunk Processing**: Extract structured data from each chunk
5. **Progress Tracking**: Store results and monitor progress
6. **Result Merging**: Combine chunks into coherent structure
7. **Validation**: Check completeness and consistency
8. **Final Storage**: Save complete structured representation

## 🤖 Agent Behavior

The orchestrator agent makes intelligent decisions about:
- Optimal chunking strategy based on document characteristics
- Sequential vs parallel chunk processing
- Handling overlapping information across chunks
- When to request human guidance for ambiguous structures
- How to merge and validate final results

## 🧪 Testing

Test with the provided sample document:
```bash
python main.py
```

The system will process `raw/UU_8_1961.txt` and create a workspace in `output/documents/`.

## 🔮 Future Enhancements

- PDF processing support
- Multi-language support
- Advanced validation rules
- Integration with external legal databases
- Web interface for document upload
- Batch processing capabilities
- Export to AkomaNtoso XML format

## 🤝 Contributing

This project is designed to be extensible. Key areas for contribution:
- Additional document type support
- Enhanced chunking strategies
- Improved validation rules
- Performance optimizations
- UI/UX improvements

## 📄 License

[Add your license information here]

## 🙏 Acknowledgments

Built using OpenAI's Agents SDK for intelligent orchestration of legal document processing workflows.
