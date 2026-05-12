#!/usr/bin/env python3
"""
Simple command-line test to verify the LLM model works.
Tests connection to Ollama and sends a simple chat completion.
"""

import sys
import os
from pathlib import Path

# Add the back directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

# Load .env file
from dotenv import load_dotenv
load_dotenv()

from src.controller.llm_factory import LLMClientFactory

def test_llm_model():
    """Test the LLM model by sending a simple completion request."""
    
    print("=" * 60)
    print("LLM Model Test")
    print("=" * 60)
    
    # Get LLM settings
    try:
        factory = LLMClientFactory()
        settings = factory.get_settings()
        print(f"\n✓ LLM Settings loaded:")
        print(f"  - URL: {settings.base_url}")
        print(f"  - Model: {settings.model}")
    except Exception as e:
        print(f"\n✗ Failed to load LLM settings: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Create LLM client
    try:
        client = factory.create_client()
        print(f"\n✓ LLM client created successfully")
    except Exception as e:
        print(f"\n✗ Failed to create LLM client: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Send a simple completion request
    print(f"\n📤 Sending test prompt to model...")
    try:
        response = client.chat(
            messages=[
                {
                    "role": "user",
                    "content": "Say 'Hello from Ollama!' in exactly 5 words."
                }
            ],
            temperature=0.7,
            max_tokens=100,
            json_mode=False,
        )
        
        print(f"\n✓ Response received successfully!")
        print(f"\n📝 Raw Response:")
        print(f"  {response}")
        
        # Extract the content from the response
        content = client.get_content_text(response)
        if content:
            print(f"\n💬 Model Output:")
            print(f"  {content}")
        
        return True
        
    except Exception as e:
        print(f"\n✗ Failed to get completion from model: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_llm_model()
    print("\n" + "=" * 60)
    if success:
        print("✓ LLM Model Test PASSED")
        sys.exit(0)
    else:
        print("✗ LLM Model Test FAILED")
        sys.exit(1)
