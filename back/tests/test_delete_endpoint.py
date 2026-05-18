#!/usr/bin/env python3
"""Test the DELETE /api/opportunities/{id} endpoint."""

import os
import requests
import sys
import pytest

RUN_MANUAL_SMOKE_TESTS = os.getenv("RUN_MANUAL_SMOKE_TESTS") == "1"

pytestmark = pytest.mark.skipif(
    not RUN_MANUAL_SMOKE_TESTS,
    reason="Manual smoke script; set RUN_MANUAL_SMOKE_TESTS=1 to execute against a live HTTP server.",
)

def test_delete_endpoint():
    """Test opportunity deletion endpoint."""
    # Mise à jour de l'URL pour utiliser le bon port
    api_url = "http://localhost:8089/api/opportunities/test-opportunity-id"
    
    # Remplacer 'your-bearer-token-here' par un jeton valide
    token = "votre-jeton-valide-ici"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    print(f"Testing DELETE {api_url}")
    print(f"Headers: {headers}")
    
    try:
        response = requests.delete(api_url, headers=headers)
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print(f"Response Body: {response.text}")
        
        if response.ok:
            print("✅ DELETE request successful!")
        else:
            print(f"❌ DELETE request failed with status {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        pytest.fail(f"Request failed: {e}")

if __name__ == "__main__":
    test_delete_endpoint()
