#!/usr/bin/env python3
"""
Agentic Workflow Engine for Legal Document Processing
Coordinates the conversion of Indonesian UU documents to structured JSON
"""

import json
import asyncio
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from pathlib import Path
import re
from datetime import datetime

# For LLM integration
# import openai
from openai import OpenAI

@dataclass
class ProcessingPlan:
    """Plan for processing a legal document"""
    document_id: str
    sections: List[str]
    processing_strategy: str
    estimated_cost: float
    complexity: str
    special_considerations: List[str]

class LegalDocumentAgent:
    """
    Agentic workflow for processing Indonesian legal documents
    Coordinates planning, memory, and execution phases
    """
    
    def __init__(self, openrouter_api_key: str, budget_limit: float = 10.0, model: str = "openai/gpt-4.1-mini"):
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=openrouter_api_key,
        )
        self.model = model
        self.budget_limit = budget_limit
        self.current_cost = 0.0
        self.memory = {}
        self.processing_plan: Optional[ProcessingPlan] = None
        
    async def analyze_and_plan(self, document_text: str, document_id: str) -> ProcessingPlan:
        """
        Phase 1: Analyze document and create processing plan
        """
        print(f"🔍 Analyzing document structure for {document_id}...")
        
        # Use Claude to analyze the document structure
        analysis_prompt = f"""
        Analyze this Indonesian legal document (UU) and create a processing plan.
        
        Document text:
        {document_text[:3000]}...
        
        Please analyze:
        1. Document structure (sections, articles, complexity)
        2. Processing strategy (which parts need careful attention)
        3. Estimated processing cost (considering $10 budget)
        4. Special considerations (cross-references, complex formatting, etc.)
        
        Respond in JSON format with your analysis.
        """
        
        # Define schema for analysis response
        analysis_schema = {
            "name": "document_analysis",
            "schema": {
                "type": "object",
                "properties": {
                    "sections": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of document sections identified"
                    },
                    "strategy": {
                        "type": "string",
                        "description": "Processing strategy (e.g., sequential, parallel)"
                    },
                    "estimated_cost": {
                        "type": "number",
                        "description": "Estimated processing cost in USD"
                    },
                    "complexity": {
                        "type": "string",
                        "enum": ["low", "medium", "high"],
                        "description": "Document complexity level"
                    },
                    "considerations": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Special considerations for processing"
                    }
                },
                "required": ["sections", "strategy", "estimated_cost", "complexity", "considerations"],
                "additionalProperties": False
            }
        }
        
        try:
            response = await self._call_llm(analysis_prompt, max_tokens=1000, schema=analysis_schema)
            analysis = json.loads(response)
            
            # Create processing plan
            plan = ProcessingPlan(
                document_id=document_id,
                sections=analysis.get("sections", []),
                processing_strategy=analysis.get("strategy", "sequential"),
                estimated_cost=analysis.get("estimated_cost", 5.0),
                complexity=analysis.get("complexity", "medium"),
                special_considerations=analysis.get("considerations", [])
            )
            
            self.processing_plan = plan
            print(f"📋 Processing plan created: {plan.complexity} complexity, ${plan.estimated_cost:.2f} estimated cost")
            return plan
            
        except Exception as e:
            print(f"❌ Error in analysis phase: {e}")
            # Fallback plan
            return ProcessingPlan(
                document_id=document_id,
                sections=["header", "menimbang", "mengingat", "pasal", "penjelasan"],
                processing_strategy="sequential",
                estimated_cost=5.0,
                complexity="medium",
                special_considerations=["manual_fallback"]
            )
    
    async def process_section(self, section_text: str, section_type: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a specific section of the document
        """
        print(f"⚙️ Processing section: {section_type}")
        
        # Build context-aware prompt
        prompt = self._build_section_prompt(section_text, section_type, context)
        
        # Get schema for this section type
        section_schema = self._get_section_schema(section_type)
        
        try:
            response = await self._call_llm(prompt, max_tokens=2000, schema=section_schema)
            print(response)
            result = json.loads(response)
            
            # Update memory with learned patterns
            self._update_memory(section_type, result)
            
            return result
            
        except Exception as e:
            print(f"❌ Error processing {section_type}: {e}")
            return {"error": str(e), "section_type": section_type}
    
    def _get_section_schema(self, section_type: str) -> Dict[str, Any]:
        """Get JSON schema for specific section type"""
        
        if section_type == "menimbang":
            return {
                "name": "menimbang_section",
                "schema": {
                    "type": "object",
                    "properties": {
                        "type": {"type": "string", "const": "menimbang"},
                        "items": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "letter": {"type": "string", "description": "Item letter (a, b, c, etc.)"},
                                    "content": {"type": "string", "description": "Content of the consideration"}
                                },
                                "required": ["letter", "content"],
                                "additionalProperties": False
                            }
                        }
                    },
                    "required": ["type", "items"],
                    "additionalProperties": False
                }
            }
            
        elif section_type == "mengingat":
            return {
                "name": "mengingat_section",
                "schema": {
                    "type": "object",
                    "properties": {
                        "type": {"type": "string", "const": "mengingat"},
                        "items": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "letter": {"type": "string", "description": "Item letter (a, b, c, etc.)"},
                                    "content": {"type": "string", "description": "Content of the reference"},
                                    "references": {
                                        "type": "array",
                                        "items": {"type": "string"},
                                        "description": "Legal references mentioned"
                                    }
                                },
                                "required": ["letter", "content", "references"],
                                "additionalProperties": False
                            }
                        }
                    },
                    "required": ["type", "items"],
                    "additionalProperties": False
                }
            }
            
        elif section_type.startswith("pasal_"):
            return {
                "name": "pasal_section",
                "schema": {
                    "type": "object",
                    "properties": {
                        "type": {"type": "string", "const": "pasal"},
                        "number": {"type": "integer", "description": "Article number"},
                        "ayat": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "number": {"type": "integer", "description": "Ayat number"},
                                    "content": {"type": "string", "description": "Ayat content"},
                                    "sub_items": {
                                        "type": "array",
                                        "items": {
                                            "type": "object",
                                            "properties": {
                                                "type": {"type": "string", "enum": ["huruf", "angka"]},
                                                "letter": {"type": "string", "description": "Letter for huruf items"},
                                                "number": {"type": "integer", "description": "Number for angka items"},
                                                "content": {"type": "string", "description": "Sub-item content"}
                                            },
                                            "required": ["type", "content", "letter", ""],
                                            "additionalProperties": False
                                        }
                                    }
                                },
                                "required": ["number", "content"],
                                "additionalProperties": False
                            }
                        },
                        "cross_references": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Cross-references to other articles"
                        }
                    },
                    "required": ["type", "number", "ayat"],
                    "additionalProperties": False
                }
            }
            
        elif section_type == "penjelasan":
            return {
                "name": "penjelasan_section",
                "schema": {
                    "type": "object",
                    "properties": {
                        "type": {"type": "string", "const": "penjelasan"},
                        "general_explanation": {"type": "string", "description": "General explanation text"},
                        "article_explanations": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "pasal_number": {"type": "integer", "description": "Article number being explained"},
                                    "explanation": {"type": "string", "description": "Explanation text"},
                                    "links_to": {
                                        "type": "array",
                                        "items": {"type": "string"},
                                        "description": "Links to other articles or sections"
                                    }
                                },
                                "required": ["pasal_number", "explanation", "links_to"],
                                "additionalProperties": False
                            }
                        }
                    },
                    "required": ["type", "general_expalantion", "article_explanation"],
                    "additionalProperties": False
                }
            }
            
        else:
            # Generic schema for other section types
            return {
                "name": "generic_section",
                "schema": {
                    "type": "object",
                    "properties": {
                        "type": {"type": "string", "description": "Section type"},
                        "content": {"type": "string", "description": "Section content"},
                        "structure": {
                            "type": "object",
                            "description": "Structured content if applicable",
                            "additionalProperties": False
                        }
                    },
                    "required": ["type", "content", "structure"],
                    "additionalProperties": False
                }
            }
    
    def _build_section_prompt(self, section_text: str, section_type: str, context: Dict[str, Any]) -> str:
        """Build context-aware prompt for section processing"""
        
        base_prompt = f"""
        You are processing a section of an Indonesian legal document (UU).
        
        Section type: {section_type}
        Section text:
        {section_text}
        
        Context from previous sections:
        {json.dumps(context.get('previous_sections', {}), indent=2)}
        
        Learned definitions:
        {json.dumps(self.memory.get('definitions', {}), indent=2)}
        
        Cross-references found:
        {json.dumps(self.memory.get('cross_references', {}), indent=2)}
        """
        
        if section_type == "menimbang":
            return base_prompt + """
            Extract the "Menimbang" (considerations) section into structured JSON.
            Pay attention to:
            - Each consideration item (usually marked with letters a, b, c, etc.)
            - The content of each consideration
            """
            
        elif section_type == "mengingat":
            return base_prompt + """
            Extract the "Mengingat" (references) section into structured JSON.
            Pay attention to:
            - Each reference item (usually marked with letters a, b, c, etc.)
            - Legal references mentioned (UUD, other laws, etc.)
            """
            
        elif section_type.startswith("pasal_"):
            return base_prompt + """
            Extract this Pasal (article) into structured JSON.
            Pay special attention to:
            - Article number
            - Hierarchical structure (ayat, huruf, angka)
            - Cross-references to other articles
            - Legal terminology that should be tracked
            """
            
        elif section_type == "penjelasan":
            return base_prompt + """
            Extract this Penjelasan (explanation) section and link it to main articles.
            Pay attention to:
            - General explanation text
            - Specific article explanations
            - Links between explanations and main articles
            """
            
        else:
            return base_prompt + """
            Extract this section into appropriate structured JSON format.
            Maintain the hierarchical structure and identify any cross-references.
            """
    
    def _update_memory(self, section_type: str, result: Dict[str, Any]):
        """Update agent memory with learned patterns"""
        
        # Track definitions
        if 'definitions' not in self.memory:
            self.memory['definitions'] = {}
            
        # Track cross-references
        if 'cross_references' not in self.memory:
            self.memory['cross_references'] = {}
            
        # Track processing patterns
        if 'patterns' not in self.memory:
            self.memory['patterns'] = {}
            
        # Extract and store cross-references
        if 'cross_references' in result:
            for ref in result['cross_references']:
                if ref not in self.memory['cross_references']:
                    self.memory['cross_references'][ref] = []
                self.memory['cross_references'][ref].append(section_type)
        
        # Store section-specific patterns
        self.memory['patterns'][section_type] = {
            'last_processed': datetime.now().isoformat(),
            'structure': result.get('type', 'unknown')
        }
    
    async def _call_llm(self, prompt: str, max_tokens: int = 1000, schema: Optional[Dict[str, Any]] = None) -> str:
        """Call LLM API via OpenRouter with cost tracking and optional structured output"""
        
        # Estimate cost (rough approximation for GPT-4o-mini via OpenRouter)
        estimated_cost = (len(prompt) + max_tokens) * 0.000005  # OpenRouter is cheaper
        
        if self.current_cost + estimated_cost > self.budget_limit:
            raise Exception(f"Budget limit exceeded. Current: ${self.current_cost:.2f}, Estimated: ${estimated_cost:.2f}")
        
        try:
            # Build request parameters
            request_params = {
                "model": self.model,
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": max_tokens,
                "temperature": 0.1  # Low temperature for consistent structured output
            }
            
            # Add structured output if schema is provided
            if schema:
                request_params["response_format"] = {
                    "type": "json_schema",
                    "json_schema": {
                        "name": schema.get("name", "response"),
                        "strict": True,
                        "schema": schema["schema"]
                    }
                }
            
            response = self.client.chat.completions.create(**request_params)
            
            self.current_cost += estimated_cost
            print(f"💰 Cost update: ${self.current_cost:.2f} / ${self.budget_limit:.2f}")
            
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"❌ LLM API error: {e}")
            raise
    
    async def process_document(self, document_text: str, document_id: str) -> Dict[str, Any]:
        """
        Main workflow: Process entire document
        """
        print(f"🚀 Starting document processing for {document_id}")
        
        # Phase 1: Analysis and Planning
        plan = await self.analyze_and_plan(document_text, document_id)
        
        # Phase 2: Section-by-section processing
        result = {
            "metadata": {
                "document_id": document_id,
                "processing_plan": plan.__dict__,
                "processing_started": datetime.now().isoformat()
            },
            "content": {}
        }
        
        # Split document into sections
        sections = self._split_document(document_text)
        
        for section_name, section_text in sections.items():
            if self.current_cost >= self.budget_limit:
                print(f"⚠️ Budget limit reached, stopping processing")
                break
                
            try:
                section_result = await self.process_section(
                    section_text, 
                    section_name, 
                    {"previous_sections": result["content"]}
                )
                result["content"][section_name] = section_result
                
            except Exception as e:
                print(f"❌ Error processing section {section_name}: {e}")
                result["content"][section_name] = {"error": str(e)}
        
        # Phase 3: Cross-reference resolution
        result = self._resolve_cross_references(result)
        
        # Final metadata
        result["metadata"]["processing_completed"] = datetime.now().isoformat()
        result["metadata"]["total_cost"] = self.current_cost
        result["metadata"]["memory_state"] = self.memory
        
        print(f"✅ Document processing completed. Total cost: ${self.current_cost:.2f}")
        return result
    
    def _split_document(self, text: str) -> Dict[str, str]:
        """Split document into logical sections"""
        sections = {}
        lines = text.split('\n')
        current_section = "header"
        current_content = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Check for section markers
            if re.match(r'^Menimbang\s*:?\s*$', line, re.IGNORECASE):
                if current_content:
                    sections[current_section] = '\n'.join(current_content)
                current_section = "menimbang"
                current_content = [line]
            elif re.match(r'^Mengingat\s*:?\s*$', line, re.IGNORECASE):
                if current_content:
                    sections[current_section] = '\n'.join(current_content)
                current_section = "mengingat"
                current_content = [line]
            elif re.match(r'^MEMUTUSKAN\s*:?\s*$', line, re.IGNORECASE):
                if current_content:
                    sections[current_section] = '\n'.join(current_content)
                current_section = "memutuskan"
                current_content = [line]
            elif re.match(r'^Pasal\s+\d+', line):
                if current_content:
                    sections[current_section] = '\n'.join(current_content)
                current_section = f"pasal_{re.search(r'Pasal\s+(\d+)', line).group(1)}"
                current_content = [line]
            elif re.match(r'^PENJELASAN$', line, re.IGNORECASE):
                if current_content:
                    sections[current_section] = '\n'.join(current_content)
                current_section = "penjelasan"
                current_content = [line]
            else:
                current_content.append(line)
        
        # Add final section
        if current_content:
            sections[current_section] = '\n'.join(current_content)
            
        return sections
    
    def _resolve_cross_references(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve cross-references between sections"""
        print("🔗 Resolving cross-references...")
        
        # Add cross-reference resolution logic here
        # For now, just add the memory state
        result["cross_reference_map"] = self.memory.get('cross_references', {})
        
        return result

# Example usage function
async def process_uu_document(document_path: str, openrouter_api_key: str) -> Dict[str, Any]:
    """Process a UU document using the agentic workflow"""
    
    # Read document
    with open(document_path, 'r', encoding='utf-8') as f:
        document_text = f.read()
    
    # Initialize agent
    agent = LegalDocumentAgent(openrouter_api_key)
    
    # Process document
    document_id = Path(document_path).stem
    result = await agent.process_document(document_text, document_id)
    
    return result

if __name__ == "__main__":
    # Example usage
    import os
    from dotenv import load_dotenv
    load_dotenv()
    
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("Please set OPENROUTER_API_KEY environment variable")
        print("Get your API key from: https://openrouter.ai/keys")
        exit(1)
    
    # Process the UU 8/1961 document
    result = asyncio.run(process_uu_document("raw/UU_8_1961.txt", api_key))
    
    # Save result
    with open("output/uu_8_1961_structured.json", "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    print("✅ Processing complete! Check output/uu_8_1961_structured.json")
