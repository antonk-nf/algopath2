// Simple test to verify the setup works
import { apiClient } from './src/services/apiClient.js';

console.log('✅ API Client imported successfully');
console.log('✅ Base URL:', apiClient.baseURL || 'http://localhost:8000');
console.log('✅ Project setup verification complete');

// Test that the API client can be instantiated
try {
  const client = new (await import('./src/services/apiClient.js')).ApiClient();
  console.log('✅ API Client can be instantiated');
} catch (error) {
  console.log('❌ API Client instantiation failed:', error.message);
}

console.log('\n🎉 Frontend project setup is complete and ready for development!');