#!/usr/bin/env python3
"""
Additional Topic Endpoint Tests
Tests edge cases and parameter combinations for comprehensive verification.
"""

import requests
import json
import time

def test_additional_parameters():
    """Test additional parameter combinations and edge cases."""
    base_url = "http://localhost:8000"
    
    print("🔍 Testing Additional Parameter Combinations")
    print("=" * 50)
    
    # Test various parameter combinations for trends endpoint
    test_cases = [
        # Empty parameters
        {},
        
        # Invalid parameters
        {'invalid_param': 'test'},
        {'period': 'invalid'},
        {'company': 'NonExistentCompany'},
        
        # Multiple parameters
        {'period': '30d', 'company': 'Google'},
        {'trending': 'up', 'period': '3m'},
        
        # Case sensitivity tests
        {'company': 'google'},  # lowercase
        {'company': 'GOOGLE'},  # uppercase
        
        # Special characters
        {'company': 'Google Inc.'},
        
        # Limit parameters (if supported)
        {'limit': 10},
        {'limit': 100},
        {'limit': 1},
    ]
    
    results = []
    
    for i, params in enumerate(test_cases, 1):
        print(f"\n{i}. Testing parameters: {params}")
        
        try:
            start_time = time.time()
            response = requests.get(f"{base_url}/api/v1/topics/trends", params=params, timeout=30)
            end_time = time.time()
            
            result = {
                'test_case': i,
                'params': params,
                'status_code': response.status_code,
                'response_time': round(end_time - start_time, 2),
                'success': response.status_code == 200,
                'record_count': 0
            }
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    if isinstance(data, list):
                        result['record_count'] = len(data)
                    elif isinstance(data, dict) and 'data' in data:
                        result['record_count'] = len(data['data'])
                    
                    print(f"   ✅ Success - {result['response_time']}s - {result['record_count']} records")
                    
                except json.JSONDecodeError:
                    result['success'] = False
                    print(f"   ❌ JSON decode error")
            else:
                print(f"   ❌ HTTP {response.status_code} - {result['response_time']}s")
                if response.text:
                    print(f"      Error: {response.text[:100]}")
            
            results.append(result)
            
        except requests.exceptions.Timeout:
            print(f"   ⏰ Timeout after 30s")
            results.append({
                'test_case': i,
                'params': params,
                'status_code': None,
                'response_time': 30,
                'success': False,
                'record_count': 0,
                'error': 'Timeout'
            })
            
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
            results.append({
                'test_case': i,
                'params': params,
                'status_code': None,
                'response_time': 0,
                'success': False,
                'record_count': 0,
                'error': str(e)
            })
    
    # Summary
    successful = sum(1 for r in results if r['success'])
    total = len(results)
    
    print(f"\n📊 SUMMARY")
    print(f"Successful tests: {successful}/{total} ({successful/total*100:.1f}%)")
    
    # Save results
    with open('additional_topic_tests_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"Results saved to: additional_topic_tests_results.json")
    
    return results

if __name__ == "__main__":
    test_additional_parameters()