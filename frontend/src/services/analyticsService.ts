import { apiClient } from './apiClient';
import { cacheService } from './cacheService';
import { staticDataService } from './staticDataService';
import type {
  AnalyticsCorrelationResponse,
  AnalyticsSummary,
  AnalyticsInsightsResponse,
  AnalyticsInsight,
  CompanyComparison
} from '../types/analytics';
import {
  FAANG_COMPANIES,
  MAJOR_TECH_COMPANIES,
  DEFAULT_ANALYTICS_CONFIG
} from '../types/analytics';

// Check if running in static mode (no API server)
const isStaticMode = (): boolean => {
  if (import.meta.env.VITE_STATIC_MODE === 'true') {
    return true;
  }
  if (import.meta.env.PROD) {
    return true;
  }
  return false;
};

class AnalyticsService {
  private cacheTimeout = DEFAULT_ANALYTICS_CONFIG.cacheTimeout * 60 * 1000; // Convert to milliseconds

  /**
   * Transform insights API response for backward compatibility
   */
  private transformAnalyticsInsights(apiResponse: any): AnalyticsInsightsResponse {
    const keyFindings = apiResponse.key_findings || [];
    const recommendations = apiResponse.recommendations || [];
    
    // Transform to backward compatible format
    const insights: AnalyticsInsight[] = [
      ...keyFindings.map((finding: any, index: number) => ({
        id: `finding_${index}`,
        type: 'pattern' as const,
        title: finding.title,
        description: finding.description,
        confidence: 0.8, // Default confidence
        actionable: true,
        metrics: finding.data,
      })),
      ...recommendations.map((rec: any, index: number) => ({
        id: `rec_${index}`,
        type: 'recommendation' as const,
        title: rec.title,
        description: rec.description,
        confidence: rec.confidence === 'high' ? 0.9 : rec.confidence === 'medium' ? 0.7 : 0.5,
        actionable: true,
        recommendation: rec.description,
      })),
    ];

    const confidenceCounts = {
      high: recommendations.filter((r: any) => r.confidence === 'high').length,
      medium: recommendations.filter((r: any) => r.confidence === 'medium').length,
      low: recommendations.filter((r: any) => r.confidence === 'low').length,
    };

    return {
      ...apiResponse,
      insights,
      totalInsights: insights.length,
      categories: ['trends', 'patterns', 'recommendations'],
      confidence: confidenceCounts,
    };
  }

  /**
   * Transform correlations API response for backward compatibility
   */
  private transformAnalyticsCorrelations(apiResponse: any): AnalyticsCorrelationResponse {
    const correlations = apiResponse.correlations || [];
    const metadata = apiResponse.metadata || {};
    
    // Calculate summary statistics
    const correlationValues = correlations.map((c: any) => Math.abs(c.correlation));
    const avgCorrelation = correlationValues.length > 0 
      ? correlationValues.reduce((a: number, b: number) => a + b, 0) / correlationValues.length 
      : 0;
    const strongCorrelations = correlationValues.filter((c: number) => c >= 0.8).length;

    const derivedMetric = metadata.analysis_type
      ? String(metadata.analysis_type).replace('_correlation', '')
      : (metadata.metric || 'composite');
    const metrics = Array.isArray(metadata.metrics)
      ? metadata.metrics
      : [derivedMetric];

    const companiesAnalyzed = Array.isArray(metadata.companies_analyzed)
      ? metadata.companies_analyzed
      : [];

    return {
      ...apiResponse,
      companies: companiesAnalyzed,
      metrics,
      summary: {
        totalPairs: correlations.length,
        avgCorrelation,
        strongCorrelations,
      },
    };
  }

  /**
   * Transform company comparison API response for backward compatibility
   */
  private transformCompanyComparison(apiResponse: any): CompanyComparison {
    const companyStats = apiResponse.company_statistics || {};
    const companies = Object.keys(companyStats);
    
    // Transform to backward compatible format
    const metrics = {
      totalProblems: {} as Record<string, number>,
      uniqueProblems: {} as Record<string, number>,
      avgFrequency: {} as Record<string, number>,
      difficultyDistribution: {} as Record<string, any>,
      topTopics: {} as Record<string, string[]>,
    };

    companies.forEach(company => {
      const stats = companyStats[company];
      metrics.totalProblems[company] = stats.total_problems;
      metrics.uniqueProblems[company] = stats.unique_problems;
      metrics.avgFrequency[company] = stats.avg_frequency;
      metrics.difficultyDistribution[company] = {
        EASY: stats.difficulty_distribution.EASY,
        MEDIUM: stats.difficulty_distribution.MEDIUM,
        HARD: stats.difficulty_distribution.HARD,
        UNKNOWN: stats.difficulty_distribution.UNKNOWN || 0,
      };
      metrics.topTopics[company] = []; // Not provided in current API
    });

    // Transform similarities
    const similarities = Object.entries(apiResponse.topic_similarities || {}).map(([key, value]: [string, any]) => {
      const [company1, company2] = key.split('_vs_');
      return {
        company1,
        company2,
        similarity: value.similarity_percentage / 100,
        commonTopics: value.common_topic_list || [],
        sharedProblems: apiResponse.problem_overlaps?.[key]?.common_problems || 0,
      };
    });

    return {
      ...apiResponse,
      companies,
      metrics,
      similarities,
      recommendations: [], // Not provided in current API, could be generated
    };
  }

  /**
   * Transform API response to expected format for backward compatibility
   */
  private transformAnalyticsSummary(apiResponse: any): AnalyticsSummary {
    const stats = apiResponse.dataset_stats || {};
    const companyBreakdown = apiResponse.company_breakdown || [];
    const topicAnalysis = apiResponse.topic_analysis || {};

    return {
      ...apiResponse,
      // Computed properties for backward compatibility
      totalCompanies: stats.unique_companies || 0,
      totalProblems: stats.total_records || 0,
      totalTopics: topicAnalysis.total_topics || 0,
      avgProblemsPerCompany: companyBreakdown.length > 0 
        ? companyBreakdown.reduce((sum: number, c: any) => sum + c.total_problems, 0) / companyBreakdown.length 
        : 0,
      difficultyDistribution: {
        EASY: stats.difficulties?.EASY || 0,
        MEDIUM: stats.difficulties?.MEDIUM || 0,
        HARD: stats.difficulties?.HARD || 0,
        UNKNOWN: stats.difficulties?.UNKNOWN || 0,
      },
      topCompanies: companyBreakdown.map((company: any, index: number) => ({
        company: company.company,
        problemCount: company.total_problems,
        rank: index + 1,
      })),
      topTopics: topicAnalysis.top_topics || [],
      timeframeCoverage: stats.timeframes || [],
    };
  }

  /**
   * Get analytics summary - fast endpoint (0.18s avg response time)
   */
  async getAnalyticsSummary(companies?: string[]): Promise<AnalyticsSummary> {
    const cacheKey = `analytics_summary_${companies?.join(',') || 'all'}`;

    // Use static data in static mode
    if (isStaticMode()) {
      try {
        const summary = await staticDataService.loadAnalyticsSummary();
        const transformedData = this.transformAnalyticsSummary(summary);
        cacheService.set(cacheKey, transformedData, 3 * 60 * 1000);
        return transformedData;
      } catch (error) {
        console.warn('Failed to load static analytics summary:', error);
      }
    }

    // Try cache first (2-3 minute cache for summary data)
    const cached = cacheService.get<AnalyticsSummary>(cacheKey);
    if (cached) {
      return cached;
    }

    try {
      const response = await apiClient.getAnalyticsSummary(companies);
      const transformedData = this.transformAnalyticsSummary(response.data);

      // Cache for 3 minutes (fast endpoint)
      cacheService.set(cacheKey, transformedData, 3 * 60 * 1000);

      return transformedData;
    } catch (error) {
      console.error('Failed to fetch analytics summary:', error);
      throw error;
    }
  }

  /**
   * Get analytics insights - moderate speed (2.40s avg response time)
   */
  async getAnalyticsInsights(companies?: string[], limit?: number): Promise<AnalyticsInsightsResponse> {
    const cacheKey = `analytics_insights_${companies?.join(',') || 'all'}_${limit || 'default'}`;

    // In static mode, return empty insights (not pre-computed)
    if (isStaticMode()) {
      return {
        key_findings: [],
        trending_topics: [],
        emerging_patterns: [],
        recommendations: [],
        metadata: {
          analysis_date: new Date().toISOString(),
          data_coverage: {
            companies: 0,
            problems: 0,
            unique_problems: 0,
            timeframes: [],
          },
        },
        insights: [],
        totalInsights: 0,
        categories: [],
        confidence: { high: 0, medium: 0, low: 0 },
      };
    }

    // Try cache first (5 minute cache for insights)
    const cached = cacheService.get<AnalyticsInsightsResponse>(cacheKey);
    if (cached) {
      return cached;
    }

    try {
      const response = await apiClient.getAnalyticsInsights(companies, limit);
      const transformedData = this.transformAnalyticsInsights(response.data);

      // Cache for 5 minutes (moderate speed endpoint)
      cacheService.set(cacheKey, transformedData, this.cacheTimeout);

      return transformedData;
    } catch (error) {
      console.error('Failed to fetch analytics insights:', error);
      throw error;
    }
  }

  /**
   * Get correlation analysis - slower endpoint (5.03s avg response time)
   * Limited to ~10 companies for performance
   */
  async getCorrelationAnalysis(companies: string[], metric: string = 'composite'): Promise<AnalyticsCorrelationResponse> {
    if (companies.length > DEFAULT_ANALYTICS_CONFIG.maxCorrelationCompanies) {
      throw new Error(`Too many companies selected. Maximum ${DEFAULT_ANALYTICS_CONFIG.maxCorrelationCompanies} allowed for correlation analysis.`);
    }

    // In static mode, return empty correlation data (not pre-computed)
    if (isStaticMode()) {
      return {
        correlations: [],
        correlation_matrix: {},
        metadata: {
          analysis_date: new Date().toISOString(),
          companies_analyzed: companies,
          correlation_method: metric,
          total_correlations: 0,
        },
        companies,
        metrics: [metric],
        summary: {
          totalPairs: 0,
          avgCorrelation: 0,
          strongCorrelations: 0,
        },
      };
    }

    const cacheKey = `analytics_correlations_${metric}_${companies.sort().join(',')}`;

    // Try cache first (10 minute cache for slow endpoint)
    const cached = cacheService.get<AnalyticsCorrelationResponse>(cacheKey);
    if (cached) {
      return cached;
    }

    try {
      const response = await apiClient.getAnalyticsCorrelations(companies, metric);
      const transformedData = this.transformAnalyticsCorrelations(response.data);

      // Cache for 10 minutes (slow endpoint)
      cacheService.set(cacheKey, transformedData, 10 * 60 * 1000);

      return transformedData;
    } catch (error) {
      console.error('Failed to fetch correlation analysis:', error);
      throw error;
    }
  }

  /**
   * Compare companies - very fast endpoint (0.14s avg response time)
   */
  async compareCompanies(companies: string[]): Promise<CompanyComparison> {
    if (companies.length < 2) {
      throw new Error('At least 2 companies required for comparison');
    }
    if (companies.length > 10) {
      throw new Error('Maximum 10 companies allowed for comparison');
    }

    // In static mode, compute comparison from static company data
    if (isStaticMode()) {
      return this.computeCompanyComparisonStatic(companies);
    }

    const cacheKey = `company_comparison_${companies.sort().join(',')}`;

    // Try cache first (5 minute cache)
    const cached = cacheService.get<CompanyComparison>(cacheKey);
    if (cached) {
      return cached;
    }

    try {
      const response = await apiClient.compareCompanies(companies);
      const transformedData = this.transformCompanyComparison(response.data);

      // Cache for 5 minutes (fast endpoint)
      cacheService.set(cacheKey, transformedData, this.cacheTimeout);

      return transformedData;
    } catch (error) {
      console.error('Failed to compare companies:', error);
      throw error;
    }
  }

  /**
   * Compute company comparison from static data
   */
  private async computeCompanyComparisonStatic(companies: string[]): Promise<CompanyComparison> {
    const allCompanyStats = await staticDataService.loadCompanyStats();

    const company_statistics: CompanyComparison['company_statistics'] = {};
    const totalProblems: Record<string, number> = {};
    const uniqueProblems: Record<string, number> = {};
    const avgFrequency: Record<string, number> = {};
    const difficultyDistribution: Record<string, { EASY: number; MEDIUM: number; HARD: number; UNKNOWN: number }> = {};
    const topTopics: Record<string, string[]> = {};

    for (const name of companies) {
      const stats = allCompanyStats.find(c =>
        c.company.toLowerCase() === name.toLowerCase()
      );
      company_statistics[name] = {
        total_problems: stats?.totalProblems || 0,
        unique_problems: stats?.uniqueProblems || 0,
        avg_frequency: stats?.avgFrequency || 0,
        avg_acceptance_rate: stats?.avgAcceptanceRate || 0,
        difficulty_distribution: stats?.difficultyDistribution || { EASY: 0, MEDIUM: 0, HARD: 0 },
        timeframe_coverage: [],
      };
      totalProblems[name] = stats?.totalProblems || 0;
      uniqueProblems[name] = stats?.uniqueProblems || 0;
      avgFrequency[name] = stats?.avgFrequency || 0;
      difficultyDistribution[name] = {
        EASY: stats?.difficultyDistribution?.EASY || 0,
        MEDIUM: stats?.difficultyDistribution?.MEDIUM || 0,
        HARD: stats?.difficultyDistribution?.HARD || 0,
        UNKNOWN: stats?.difficultyDistribution?.UNKNOWN || 0,
      };
      topTopics[name] = stats?.topTopics || [];
    }

    return {
      company_statistics,
      problem_overlaps: {},
      topic_similarities: {},
      summary: {
        companies_compared: companies.length,
        total_problems_across_companies: Object.values(totalProblems).reduce((a, b) => a + b, 0),
        most_similar_pair: [companies[0] || '', null],
        least_similar_pair: [companies[0] || '', null],
      },
      companies,
      metrics: {
        totalProblems,
        uniqueProblems,
        avgFrequency,
        difficultyDistribution,
        topTopics,
      },
      similarities: [],
      recommendations: [],
    };
  }

  /**
   * Get FAANG-specific analytics
   */
  async getFaangAnalytics(): Promise<{
    summary: AnalyticsSummary;
    insights: AnalyticsInsightsResponse;
    comparison: CompanyComparison;
    correlations?: AnalyticsCorrelationResponse;
  }> {
    const faangCompanies = [...FAANG_COMPANIES];
    
    try {
      // Run requests in parallel for better performance
      const [summary, insights, comparison] = await Promise.all([
        this.getAnalyticsSummary(faangCompanies),
        this.getAnalyticsInsights(faangCompanies, 15),
        this.compareCompanies(faangCompanies)
      ]);

      // Try to get correlations, but don't fail if it doesn't work
      let correlations: AnalyticsCorrelationResponse | undefined;
      try {
        correlations = await this.getCorrelationAnalysis(faangCompanies);
      } catch (error) {
        console.warn('FAANG correlation analysis failed:', error);
      }

      return {
        summary,
        insights,
        comparison,
        correlations
      };
    } catch (error) {
      console.error('Failed to fetch FAANG analytics:', error);
      throw error;
    }
  }

  /**
   * Get major tech companies analytics (includes Microsoft)
   */
  async getMajorTechAnalytics(): Promise<{
    summary: AnalyticsSummary;
    insights: AnalyticsInsightsResponse;
    comparison: CompanyComparison;
  }> {
    // Use top 5 major tech companies to stay within correlation limits
    const majorTechCompanies = [...MAJOR_TECH_COMPANIES].slice(0, 5);
    
    try {
      const [summary, insights, comparison] = await Promise.all([
        this.getAnalyticsSummary(majorTechCompanies),
        this.getAnalyticsInsights(majorTechCompanies, 12),
        this.compareCompanies(majorTechCompanies)
      ]);

      return {
        summary,
        insights,
        comparison
      };
    } catch (error) {
      console.error('Failed to fetch major tech analytics:', error);
      throw error;
    }
  }

  /**
   * Clear analytics cache
   */
  clearCache(): void {
    // For now, we'll clear the cache service entirely
    // In a production app, we'd implement more granular cache clearing
    cacheService.clear();
  }

  /**
   * Get cache statistics for analytics
   */
  getCacheStats(): { totalItems: number; totalSize: number } {
    return cacheService.getCacheStats();
  }
}

export const analyticsService = new AnalyticsService();
