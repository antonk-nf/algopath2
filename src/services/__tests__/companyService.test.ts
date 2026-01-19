// Simple test to verify API response transformation
import { CompanyService } from '../companyService';

describe('CompanyService', () => {
  let companyService: CompanyService;

  beforeEach(() => {
    companyService = new CompanyService();
  });

  describe('transformApiResponseToCompanyData', () => {
    it('should transform API response with nested structure', () => {
      const apiResponse = {
        company_stats: {
          company: 'Google',
          total_problems: 150,
          unique_problems: 120,
          avg_frequency: 2.8,
          avg_acceptance_rate: 0.65,
          difficulty_distribution: {
            Easy: 30,
            Medium: 70,
            Hard: 50
          },
          top_topics: {
            'Arrays': 45,
            'Dynamic Programming': 38,
            'Trees': 32
          },
          timeframes_available: ['30d', '3m', '6m']
        }
      };

      // Access the private method for testing
      const result = (companyService as any).transformApiResponseToCompanyData(apiResponse, 'Google');

      expect(result).toEqual({
        company: 'Google',
        totalProblems: 150,
        uniqueProblems: 120,
        avgFrequency: 2.8,
        avgAcceptanceRate: 0.65,
        difficultyDistribution: {
          EASY: 30,
          MEDIUM: 70,
          HARD: 50,
          UNKNOWN: 0
        },
        topTopics: ['Arrays', 'Dynamic Programming', 'Trees'],
        timeframeCoverage: ['30d', '3m', '6m'],
        rank: undefined
      });
    });

    it('should handle already transformed data', () => {
      const alreadyTransformed = {
        company: 'Amazon',
        totalProblems: 140,
        uniqueProblems: 110,
        avgFrequency: 2.5,
        avgAcceptanceRate: 0.58,
        difficultyDistribution: {
          EASY: 25,
          MEDIUM: 80,
          HARD: 35,
          UNKNOWN: 0
        },
        topTopics: ['Arrays', 'Trees'],
        timeframeCoverage: ['30d', '3m'],
        rank: 2
      };

      const result = (companyService as any).transformApiResponseToCompanyData(alreadyTransformed, 'Amazon');

      expect(result).toEqual(alreadyTransformed);
    });

    it('should handle missing difficulty distribution', () => {
      const apiResponse = {
        company_stats: {
          company: 'TestCompany',
          total_problems: 50,
          unique_problems: 40,
          avg_frequency: 1.5,
          avg_acceptance_rate: 0.70
        }
      };

      const result = (companyService as any).transformApiResponseToCompanyData(apiResponse, 'TestCompany');

      expect(result.difficultyDistribution).toEqual({
        EASY: 0,
        MEDIUM: 0,
        HARD: 0,
        UNKNOWN: 0
      });
    });
  });
});