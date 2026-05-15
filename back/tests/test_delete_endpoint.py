#!/usr/bin/env python3
"""Test the DELETE /api/opportunities/{id} endpoint."""

import requests
import sys

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
        sys.exit(1)

if __name__ == "__main__":
    test_delete_endpoint()
