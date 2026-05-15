#!/usr/bin/env python3
"""
Simple integration test to verify the file upload endpoint works
Run this while the server is running: python test_upload_integration.py
"""
import sys
import json
import requests
from pathlib import Path
from io import BytesIO

BASE_URL = "http://192.168.1.5:8088"

def test_upload():
    """Test file upload to /api/csv/source endpoint"""
    
    # Create a simple test CSV
    file_content = "name,value\ntest1,100\ntest2,200"
    files = {
        'file': ('test_upload.csv', BytesIO(file_content.encode()), 'text/csv')
    }
    
    print(f"Uploading file to {BASE_URL}/api/csv/source...")
    try:
        response = requests.post(
            f"{BASE_URL}/api/csv/source",
            files=files,
            timeout=5
        )
        
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Upload successful!")
            print(f"  Source: {data.get('source')}")
            print(f"  Path: {data.get('path')}")
            return True
        else:
            print(f"✗ Upload failed with status {response.status_code}")
            return False
    
    except requests.exceptions.ConnectionError:
        print(f"✗ Cannot connect to server at {BASE_URL}")
        print("Make sure the server is running: python back/src/rag/rag.py")
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

if __name__ == "__main__":
    success = test_upload()
    sys.exit(0 if success else 1)
