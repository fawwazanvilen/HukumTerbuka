#!/usr/bin/env python3
"""
MCP Server for Indonesian Legal Document Processing
Handles UU (Undang-Undang) conversion to structured JSON format
"""

import json
import asyncio
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from pathlib import Path
import re
from datetime import datetime

# MCP imports
from mcp.server import Server
from mcp.types import Tool, TextContent, ImageContent
import mcp.server.stdio

# Document processing state
@dataclass
class DocumentState:
    """Maintains state during document processing"""
    document_id: str
    current_section: str
    processed_sections: List[str]
    json_state: Dict[str, Any]
    cross_references: Dict[str, List[str]]
    definitions: Dict[str, str]
    processing_costs: float
    errors: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class ProcessingMetrics:
    """Track processing costs and performance"""
    total_cost: float = 0.0
    ocr_operations: int = 0
    vision_operations: int = 0
    llm_calls: int = 0
    start_time: Optional[datetime] = None
    
class LegalDocumentProcessor:
    """Core processor for Indonesian legal documents"""
    
    def __init__(self):
        self.state: Optional[DocumentState] = None
        self.metrics = ProcessingMetrics()
        self.legal_patterns = self._init_legal_patterns()
    
    def _init_legal_patterns(self) -> Dict[str, str]:
        """Initialize regex patterns for Indonesian legal structure"""
        return {
            'bab': r'^BAB\s+([IVXLC]+)\s*(.*)$',
            'bagian': r'^Bagian\s+(\w+)\s*(.*)$',
            'pasal': r'^Pasal\s+(\d+)\.?\s*$',
            'ayat': r'^\((\d+)\)',
            'huruf': r'^([a-z])\.?\s+',
            'angka': r'^(\d+)\.?\s+',
            'menimbang': r'^Menimbang\s*:',
            'mengingat': r'^Mengingat\s*:',
            'memutuskan': r'^MEMUTUSKAN\s*:?\s*$',
            'penjelasan': r'^PENJELASAN$'
        }
    
    def initialize_document(self, document_path: str, document_id: str) -> Dict[str, Any]:
        """Initialize processing for a new document"""
        self.state = DocumentState(
            document_id=document_id,
            current_section="header",
            processed_sections=[],
            json_state={
                "metadata": {
                    "document_id": document_id,
                    "document_type": "UU",
                    "processing_started": datetime.now().isoformat()
                },
                "structure": {},
                "content": {}
            },
            cross_references={},
            definitions={},
            processing_costs=0.0,
            errors=[]
        )
        self.metrics.start_time = datetime.now()
        return {"status": "initialized", "document_id": document_id}
    
    def analyze_document_structure(self, text: str) -> Dict[str, Any]:
        """Analyze overall document structure for planning"""
        structure_map = {
            "sections_found": [],
            "pasal_count": 0,
            "has_penjelasan": False,
            "complexity_estimate": "low"
        }
        
        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Check for major sections
            if re.match(self.legal_patterns['menimbang'], line, re.IGNORECASE):
                structure_map["sections_found"].append("menimbang")
            elif re.match(self.legal_patterns['mengingat'], line, re.IGNORECASE):
                structure_map["sections_found"].append("mengingat")
            elif re.match(self.legal_patterns['memutuskan'], line, re.IGNORECASE):
                structure_map["sections_found"].append("memutuskan")
            elif re.match(self.legal_patterns['penjelasan'], line, re.IGNORECASE):
                structure_map["has_penjelasan"] = True
                structure_map["sections_found"].append("penjelasan")
            elif re.match(self.legal_patterns['pasal'], line):
                structure_map["pasal_count"] += 1
        
        # Estimate complexity
        if structure_map["pasal_count"] > 20 or structure_map["has_penjelasan"]:
            structure_map["complexity_estimate"] = "medium"
        if structure_map["pasal_count"] > 50:
            structure_map["complexity_estimate"] = "high"
            
        return structure_map
    
    def get_processing_status(self) -> Dict[str, Any]:
        """Get current processing status"""
        if not self.state:
            return {"status": "not_initialized"}
            
        return {
            "document_id": self.state.document_id,
            "current_section": self.state.current_section,
            "processed_sections": self.state.processed_sections,
            "total_sections": len(self.state.processed_sections),
            "processing_costs": self.state.processing_costs,
            "errors": self.state.errors,
            "metrics": asdict(self.metrics)
        }
    
    def update_processing_cost(self, operation_type: str, cost: float) -> Dict[str, Any]:
        """Update processing costs"""
        if self.state:
            self.state.processing_costs += cost
        self.metrics.total_cost += cost
        
        if operation_type == "ocr":
            self.metrics.ocr_operations += 1
        elif operation_type == "vision":
            self.metrics.vision_operations += 1
        elif operation_type == "llm":
            self.metrics.llm_calls += 1
            
        return {"total_cost": self.metrics.total_cost, "operation": operation_type}
    
    def save_state(self, filepath: str) -> Dict[str, Any]:
        """Save current processing state"""
        if not self.state:
            return {"error": "No state to save"}
            
        state_data = {
            "state": self.state.to_dict(),
            "metrics": asdict(self.metrics),
            "timestamp": datetime.now().isoformat()
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(state_data, f, indent=2, ensure_ascii=False)
            
        return {"status": "saved", "filepath": filepath}
    
    def load_state(self, filepath: str) -> Dict[str, Any]:
        """Load processing state from file"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                state_data = json.load(f)
                
            # Reconstruct state objects
            state_dict = state_data["state"]
            self.state = DocumentState(**state_dict)
            
            metrics_dict = state_data["metrics"]
            self.metrics = ProcessingMetrics(**metrics_dict)
            
            return {"status": "loaded", "document_id": self.state.document_id}
        except Exception as e:
            return {"error": f"Failed to load state: {str(e)}"}

# Initialize the MCP server
server = Server("legal-document-processor")
processor = LegalDocumentProcessor()

@server.list_tools()
async def list_tools() -> List[Tool]:
    """List available tools for legal document processing"""
    return [
        Tool(
            name="initialize_document",
            description="Initialize processing for a new legal document",
            inputSchema={
                "type": "object",
                "properties": {
                    "document_path": {"type": "string", "description": "Path to the document file"},
                    "document_id": {"type": "string", "description": "Unique identifier for the document"}
                },
                "required": ["document_path", "document_id"]
            }
        ),
        Tool(
            name="analyze_structure",
            description="Analyze the overall structure of a legal document for processing planning",
            inputSchema={
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "Full text of the document to analyze"}
                },
                "required": ["text"]
            }
        ),
        Tool(
            name="get_status",
            description="Get current processing status and progress",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="update_cost",
            description="Update processing costs for budget tracking",
            inputSchema={
                "type": "object",
                "properties": {
                    "operation_type": {"type": "string", "enum": ["ocr", "vision", "llm"], "description": "Type of operation"},
                    "cost": {"type": "number", "description": "Cost in USD"}
                },
                "required": ["operation_type", "cost"]
            }
        ),
        Tool(
            name="save_state",
            description="Save current processing state to file",
            inputSchema={
                "type": "object",
                "properties": {
                    "filepath": {"type": "string", "description": "Path to save state file"}
                },
                "required": ["filepath"]
            }
        ),
        Tool(
            name="load_state",
            description="Load processing state from file",
            inputSchema={
                "type": "object",
                "properties": {
                    "filepath": {"type": "string", "description": "Path to state file"}
                },
                "required": ["filepath"]
            }
        )
    ]

@server.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle tool calls"""
    try:
        if name == "initialize_document":
            result = processor.initialize_document(
                arguments["document_path"], 
                arguments["document_id"]
            )
        elif name == "analyze_structure":
            result = processor.analyze_document_structure(arguments["text"])
        elif name == "get_status":
            result = processor.get_processing_status()
        elif name == "update_cost":
            result = processor.update_processing_cost(
                arguments["operation_type"], 
                arguments["cost"]
            )
        elif name == "save_state":
            result = processor.save_state(arguments["filepath"])
        elif name == "load_state":
            result = processor.load_state(arguments["filepath"])
        else:
            result = {"error": f"Unknown tool: {name}"}
            
        return [TextContent(type="text", text=json.dumps(result, indent=2, ensure_ascii=False))]
        
    except Exception as e:
        error_result = {"error": f"Tool execution failed: {str(e)}"}
        return [TextContent(type="text", text=json.dumps(error_result, indent=2))]

async def main():
    """Run the MCP server"""
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )

if __name__ == "__main__":
    asyncio.run(main())
