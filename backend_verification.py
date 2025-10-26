#!/usr/bin/env python3
"""
Backend Verification Script for Interview Prep Dashboard Phase 1
Tests API endpoints for reliability, response times, and error patterns.
"""

import requests
import time
import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class EndpointTest:
    """Test result for a single endpoint."""
    endpoint: str
    method: str
    status_code: Optional[int] = None
    response_time_ms: Optional[float] = None
    response_size_bytes: Optional[int] = None
    error: Optional[str] = None
    response_data: Optional[Dict] = None
    timeout: bool = False


class BackendVerifier:
    """Verifies backend API endpoints for Phase 1 requirements."""
    
    def __init__(self, base_url: str = "http://localhost:8000", timeout: int = 45):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.results: List[EndpointTest] = []
    
    def test_endpoint(self, endpoint: str, method: str = "GET", 
                     params: Optional[Dict] = None) -> EndpointTest:
        """Test a single endpoint and measure performance."""
        url = f"{self.base_url}{endpoint}"
        test = EndpointTest(endpoint=endpoint, method=method)
        
        try:
            start_time = time.time()
            
            response = requests.request(
                method, url, 
                params=params, 
                timeout=self.timeout
            )
            
            end_time = time.time()
            
            test.status_code = response.status_code
            test.response_time_ms = (end_time - start_time) * 1000
            test.response_size_bytes = len(response.content)
            
            # Get response data
            try:
                if response.headers.get('content-type', '').startswith('application/json'):
                    test.response_data = response.json()
                else:
                    test.response_data = {"raw_response": response.text[:500]}  # Truncate for display
            except Exception as e:
                test.error = f"Failed to parse response: {str(e)}"
                        
        except requests.exceptions.Timeout:
            test.timeout = True
            test.error = f"Request timed out after {self.timeout} seconds"
        except requests.exceptions.ConnectionError:
            test.error = "Connection refused - API server may not be running"
        except Exception as e:
            test.error = f"Request failed: {str(e)}"
        
        self.results.append(test)
        return test
    
    def verify_health_endpoints(self):
        """Test health endpoints for reliability."""
        print("🔍 Testing Health Endpoints...")
        
        # Test quick health check
        test = self.test_endpoint("/api/v1/health/quick")
        self.print_test_result("Health Quick Check", test)
        
        # Test detailed health check
        test = self.test_endpoint("/api/v1/health/data")
        self.print_test_result("Health Data Check", test)
    
    def verify_companies_endpoints(self):
        """Test companies endpoints for response shape and timeout behavior."""
        print("\n🏢 Testing Companies Endpoints...")
        
        # Test companies stats endpoint
        test = self.test_endpoint("/api/v1/companies/stats")
        self.print_test_result("Companies Stats", test)
        
        # Test specific companies
        companies = ["Google", "Amazon", "Microsoft", "Meta", "Apple"]
        for company in companies:
            test = self.test_endpoint(f"/api/v1/companies/{company}")
            self.print_test_result(f"Company: {company}", test)
    
    def verify_all_endpoints(self):
        """Run complete verification of Phase 1 endpoints."""
        print("🚀 Starting Backend Verification for Phase 1")
        print(f"Base URL: {self.base_url}")
        print(f"Timeout: {self.timeout} seconds")
        print("=" * 60)
        
        self.verify_health_endpoints()
        self.verify_companies_endpoints()
        
        print("\n" + "=" * 60)
        self.print_summary()
    
    def print_test_result(self, name: str, test: EndpointTest):
        """Print formatted test result."""
        status_icon = "✅" if test.status_code == 200 else "❌" if test.error else "⚠️"
        
        print(f"{status_icon} {name}")
        print(f"   Endpoint: {test.endpoint}")
        
        if test.timeout:
            print(f"   Status: TIMEOUT ({self.timeout}s)")
        elif test.status_code:
            print(f"   Status: {test.status_code}")
        
        if test.response_time_ms:
            print(f"   Response Time: {test.response_time_ms:.0f}ms")
        
        if test.response_size_bytes:
            print(f"   Response Size: {test.response_size_bytes:,} bytes")
        
        if test.error:
            print(f"   Error: {test.error}")
        
        # Show sample response data for successful requests
        if test.response_data and test.status_code == 200:
            if isinstance(test.response_data, dict):
                # Show structure for complex responses
                if 'data' in test.response_data:
                    data = test.response_data['data']
                    if isinstance(data, list) and len(data) > 0:
                        print(f"   Data Count: {len(data)} items")
                        print(f"   Sample Keys: {list(data[0].keys()) if isinstance(data[0], dict) else 'N/A'}")
                    else:
                        print(f"   Response Keys: {list(test.response_data.keys())}")
                else:
                    print(f"   Response Keys: {list(test.response_data.keys())}")
        
        print()
    
    def print_summary(self):
        """Print verification summary."""
        total_tests = len(self.results)
        successful_tests = len([r for r in self.results if r.status_code == 200])
        timeout_tests = len([r for r in self.results if r.timeout])
        error_tests = len([r for r in self.results if r.error and not r.timeout])
        
        print("📊 VERIFICATION SUMMARY")
        print(f"Total Tests: {total_tests}")
        print(f"Successful: {successful_tests}")
        print(f"Timeouts: {timeout_tests}")
        print(f"Errors: {error_tests}")
        print(f"Success Rate: {(successful_tests/total_tests)*100:.1f}%")
        
        # Response time analysis
        response_times = [r.response_time_ms for r in self.results if r.response_time_ms]
        if response_times:
            avg_time = sum(response_times) / len(response_times)
            max_time = max(response_times)
            min_time = min(response_times)
            print(f"\nResponse Time Analysis:")
            print(f"Average: {avg_time:.0f}ms")
            print(f"Min: {min_time:.0f}ms")
            print(f"Max: {max_time:.0f}ms")
        
        # Error patterns
        errors = [r.error for r in self.results if r.error]
        if errors:
            print(f"\nError Patterns:")
            error_counts = {}
            for error in errors:
                error_type = error.split(':')[0] if ':' in error else error
                error_counts[error_type] = error_counts.get(error_type, 0) + 1
            
            for error_type, count in error_counts.items():
                print(f"  {error_type}: {count} occurrences")
        
        # Recommendations
        print(f"\n💡 RECOMMENDATIONS:")
        
        if timeout_tests > 0:
            print("- ⚠️  Some endpoints are timing out - consider implementing loading states")
        
        if successful_tests < total_tests:
            print("- ⚠️  Some endpoints are failing - implement error handling and fallbacks")
        
        if response_times and max(response_times) > 5000:
            print("- ⚠️  Slow response times detected - implement caching strategy")
        
        if successful_tests == total_tests:
            print("- ✅ All endpoints working - ready for Phase 1 implementation")
    
    def save_results(self, filename: str = "backend_verification_results.json"):
        """Save verification results to JSON file."""
        results_data = {
            "timestamp": datetime.now().isoformat(),
            "base_url": self.base_url,
            "timeout": self.timeout,
            "results": []
        }
        
        for result in self.results:
            results_data["results"].append({
                "endpoint": result.endpoint,
                "method": result.method,
                "status_code": result.status_code,
                "response_time_ms": result.response_time_ms,
                "response_size_bytes": result.response_size_bytes,
                "error": result.error,
                "timeout": result.timeout,
                "response_data_keys": list(result.response_data.keys()) if result.response_data else None
            })
        
        with open(filename, 'w') as f:
            json.dump(results_data, f, indent=2)
        
        print(f"\n💾 Results saved to {filename}")


def main():
    """Main verification function."""
    verifier = BackendVerifier()
    verifier.verify_all_endpoints()
    verifier.save_results()


if __name__ == "__main__":
    main()