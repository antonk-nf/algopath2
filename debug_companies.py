#!/usr/bin/env python3
"""
Debug company validation
"""

import requests
import json

def debug_companies():
    base_url = "http://localhost:8000"
    
    # First, get the list of available companies
    print("Getting available companies...")
    try:
        response = requests.get(f"{base_url}/api/v1/companies/stats?limit=5")
        if response.status_code == 200:
            data = response.json()
            companies = [item['company'] for item in data['data']]
            print(f"Available companies: {companies}")
            
            # Test with single company
            print(f"\nTesting with single company: {companies[0]}")
            response = requests.get(
                f"{base_url}/api/v1/analytics/correlations",
                params={"companies": [companies[0]]},
                timeout=30
            )
            print(f"Single company status: {response.status_code}")
            if response.status_code != 200:
                print(f"Error: {response.text[:300]}")
            
            # Test with two companies
            print(f"\nTesting with two companies: {companies[0]}, {companies[1]}")
            response = requests.get(
                f"{base_url}/api/v1/analytics/correlations",
                params={"companies": [companies[0], companies[1]]},
                timeout=30
            )
            print(f"Two companies status: {response.status_code}")
            if response.status_code != 200:
                print(f"Error: {response.text[:300]}")
                
        else:
            print(f"Failed to get companies: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    debug_companies()