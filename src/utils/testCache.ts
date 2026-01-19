import { cacheService } from '../services/cacheService';
import type { CompanyData } from '../types/company';

// Simple test function to verify cache functionality
export function testCacheService() {
  console.log('Testing cache service...');

  // Test basic set/get
  const testData = { test: 'data', timestamp: Date.now() };
  cacheService.set('test_key', testData);
  const retrieved = cacheService.get<typeof testData>('test_key');
  console.log('Basic cache test:', retrieved?.test === 'data' ? 'PASS' : 'FAIL');

  // Test company data caching
  const mockCompany: CompanyData = {
    company: 'Test Company',
    totalProblems: 100,
    uniqueProblems: 80,
    avgFrequency: 2.5,
    avgAcceptanceRate: 0.65,
    difficultyDistribution: {
      EASY: 30,
      MEDIUM: 50,
      HARD: 20,
      UNKNOWN: 0
    },
    topTopics: ['Arrays', 'Strings'],
    timeframeCoverage: ['30d'],
    rank: 1
  };

  cacheService.setCompanyDetail('test-company', mockCompany);
  const retrievedCompany = cacheService.getCompanyDetail('test-company');
  console.log('Company cache test:', retrievedCompany?.company === 'Test Company' ? 'PASS' : 'FAIL');

  // Test cache stats
  const stats = cacheService.getCacheStats();
  console.log('Cache stats:', stats);

  // Cleanup
  cacheService.remove('test_key');
  cacheService.remove('company_detail_test-company');
  
  console.log('Cache service tests completed');
}