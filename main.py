#!/usr/bin/env python3
"""
HukumTerbuka - Legal Document Processing System
Main entry point for testing the orchestrator agent.
"""

import asyncio
import os
import json
from datetime import datetime
from dotenv import load_dotenv
from hukum_agents import process_legal_document, quick_process

def debug_print(message, level="INFO"):
    """Print debug messages with timestamp and level."""
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    print(f"[{timestamp}] [{level}] {message}")

async def main():
    """Main function to test the legal document processing system."""
    
    debug_print("🚀 Starting HukumTerbuka Legal Document Processing System")
    
    # Load environment variables
    debug_print("📋 Loading environment variables...")
    load_dotenv()
    
    # Check if OpenAI API key is set
    api_key = os.getenv("OPENAI_API_KEY") or os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        debug_print("❌ No API key found in environment variables!", "ERROR")
        print("Please set your OpenAI/OpenRouter API key in the .env file")
        return
    else:
        debug_print(f"✅ API key found: {api_key[:10]}...{api_key[-4:]}")
    
    print("\n🏛️  HukumTerbuka - Legal Document Processing System")
    print("=" * 60)
    
    # Check if sample document exists
    sample_file = "raw/UU_8_1961.txt"
    debug_print(f"📁 Checking for sample document: {sample_file}")
    
    if not os.path.exists(sample_file):
        debug_print(f"❌ Sample document not found: {sample_file}", "ERROR")
        print("Please ensure the sample document exists in the raw/ directory")
        return
    
    # Get file info
    file_size = os.path.getsize(sample_file)
    debug_print(f"📄 Document found - Size: {file_size:,} bytes")
    
    print(f"📄 Processing sample document: {sample_file}")
    print("🤖 Starting orchestrator agent...")
    print("-" * 60)
    
    try:
        debug_print("🔄 Calling quick_process function...")
        
        # Process the document
        result = await quick_process(sample_file)
        
        debug_print("📤 Received result from quick_process")
        debug_print(f"🔍 Result keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")
        
        if result.get("success"):
            debug_print("✅ Processing marked as successful!")
            print("✅ Document processing completed successfully!")
            print(f"📁 Workspace: {result.get('workspace_path', 'N/A')}")
            print(f"🆔 Document ID: {result.get('document_id', 'N/A')}")
            
            # Show detailed result
            if "result" in result:
                print("\n📋 Processing Result:")
                print("-" * 40)
                if isinstance(result["result"], dict):
                    print(json.dumps(result["result"], indent=2, ensure_ascii=False))
                else:
                    print(result["result"])
            
            # Show workspace status if available
            if "workspace_status" in result:
                print("\n📊 Workspace Status:")
                print("-" * 40)
                print(json.dumps(result["workspace_status"], indent=2, ensure_ascii=False))
                
        else:
            debug_print("❌ Processing marked as failed!", "ERROR")
            print("❌ Document processing failed!")
            error_msg = result.get('error', 'Unknown error')
            print(f"Error: {error_msg}")
            
            # Show additional debug info if available
            if "debug_info" in result:
                debug_print("🔍 Additional debug information:")
                print(json.dumps(result["debug_info"], indent=2, ensure_ascii=False))
            
    except Exception as e:
        debug_print(f"💥 Unexpected exception occurred: {str(e)}", "ERROR")
        print(f"❌ Unexpected error: {str(e)}")
        import traceback
        debug_print("📋 Full traceback:", "ERROR")
        traceback.print_exc()

def run_interactive():
    """Interactive mode for processing custom documents."""
    print("🏛️  HukumTerbuka - Interactive Mode")
    print("=" * 50)
    
    while True:
        print("\nOptions:")
        print("1. Process sample document (UU_8_1961.txt)")
        print("2. Process custom document")
        print("3. Show debug info")
        print("4. Exit")
        
        choice = input("\nEnter your choice (1-4): ").strip()
        
        if choice == "1":
            asyncio.run(main())
        elif choice == "2":
            file_path = input("Enter document path: ").strip()
            if os.path.exists(file_path):
                async def process_custom():
                    debug_print(f"🔄 Processing custom document: {file_path}")
                    result = await process_legal_document(file_path)
                    debug_print(f"📤 Custom processing result: {result}")
                    
                    if result.get("success"):
                        print("✅ Processing completed!")
                        print(f"📁 Workspace: {result.get('workspace_path', 'N/A')}")
                    else:
                        print(f"❌ Error: {result.get('error', 'Unknown error')}")
                
                asyncio.run(process_custom())
            else:
                print(f"❌ File not found: {file_path}")
        elif choice == "3":
            print("\n🔍 Debug Information:")
            print("-" * 30)
            print(f"Current working directory: {os.getcwd()}")
            print(f"Python path: {os.sys.path[0]}")
            print(f"Environment variables:")
            for key in ["OPENAI_API_KEY", "OPENROUTER_API_KEY", "OPENAI_MODEL"]:
                value = os.getenv(key)
                if value:
                    print(f"  {key}: {value[:10]}...{value[-4:] if len(value) > 14 else value}")
                else:
                    print(f"  {key}: Not set")
            
            # Check output directory
            if os.path.exists("output"):
                print(f"\nOutput directory contents:")
                for root, dirs, files in os.walk("output"):
                    level = root.replace("output", "").count(os.sep)
                    indent = " " * 2 * level
                    print(f"{indent}{os.path.basename(root)}/")
                    subindent = " " * 2 * (level + 1)
                    for file in files:
                        print(f"{subindent}{file}")
            else:
                print("\nOutput directory does not exist")
                
        elif choice == "4":
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice. Please enter 1, 2, 3, or 4.")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--interactive":
        run_interactive()
    else:
        asyncio.run(main())
