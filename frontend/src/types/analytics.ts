// Analytics data types based on the backend verification results

export interface AnalyticsCorrelation {
  company1: string;
  company2: string;
  correlation: number;
  metric: string;
  strength: 'weak' | 'moderate' | 'strong';
  significance?: number;
}

export interface AnalyticsCorrelationResponse {
  correlations: Array<{
    company1: string;
    company2: string;
    correlation: number;
  }>;
  correlation_matrix: Record<string, Record<string, number>>;
  metadata: {
    analysis_date: string;
    companies_analyzed: string[];
    correlation_method: string;
    total_correlations: number;
  };
  // Computed properties for backward compatibility
  companies: string[];
  metrics: string[];
  summary: {
    totalPairs: number;
    avgCorrelation: number;
    strongCorrelations: number;
  };
}

export interface AnalyticsSummary {
  dataset_stats: {
    total_records: number;
    unique_problems: number;
    unique_companies: number;
    timeframes: string[];
    difficulties: {
      EASY: number;
      MEDIUM: number;
      HARD: number;
      UNKNOWN?: number;
    };
    date_range: {
      earliest: string;
      latest: string;
    };
  };
  top_metrics: {
    most_frequent_problem: string;
    highest_acceptance_rate: string;
    most_common_difficulty: string;
    most_active_timeframe: string;
  };
  company_breakdown?: Array<{
    company: string;
    total_problems: number;
    unique_problems: number;
    avg_frequency: number;
  }>;
  topic_analysis?: {
    total_topics: number;
    top_topics: Array<{
      topic: string;
      frequency: number;
      companies: number;
    }>;
  };
  // Computed properties for backward compatibility
  totalCompanies: number;
  totalProblems: number;
  totalTopics: number;
  avgProblemsPerCompany: number;
  difficultyDistribution: {
    EASY: number;
    MEDIUM: number;
    HARD: number;
    UNKNOWN: number;
  };
  topCompanies: Array<{
    company: string;
    problemCount: number;
    rank: number;
  }>;
  topTopics: Array<{
    topic: string;
    frequency: number;
    companies: number;
  }>;
  timeframeCoverage: string[];
}

export interface AnalyticsInsight {
  id: string;
  type: 'trend' | 'pattern' | 'recommendation' | 'anomaly';
  title: string;
  description: string;
  confidence: number;
  actionable: boolean;
  companies?: string[];
  topics?: string[];
  metrics?: Record<string, number>;
  recommendation?: string;
}

export interface AnalyticsInsightsResponse {
  key_findings: Array<{
    type: string;
    title: string;
    description: string;
    data: any;
  }>;
  trending_topics: Array<{
    topic: string;
    total_frequency: number;
    trend_direction: 'increasing' | 'decreasing' | 'stable';
    trend_strength: number;
    timeframe_data: Record<string, number>;
  }>;
  emerging_patterns: any[];
  recommendations: Array<{
    type: string;
    title: string;
    description: string;
    action: string;
    confidence: 'high' | 'medium' | 'low';
  }>;
  metadata: {
    analysis_date: string;
    data_coverage: {
      companies: number;
      problems: number;
      unique_problems: number;
      timeframes: string[];
    };
  };
  // Computed properties for backward compatibility
  insights: AnalyticsInsight[];
  totalInsights: number;
  categories: string[];
  confidence: {
    high: number;
    medium: number;
    low: number;
  };
}

export interface CompanyComparison {
  company_statistics: Record<string, {
    total_problems: number;
    unique_problems: number;
    avg_frequency: number;
    avg_acceptance_rate: number;
    difficulty_distribution: {
      EASY: number;
      MEDIUM: number;
      HARD: number;
      UNKNOWN?: number;
    };
    timeframe_coverage: string[];
  }>;
  problem_overlaps: Record<string, {
    common_problems: number;
    total_unique_problems: number;
    overlap_percentage: number;
    company1_unique: number;
    company2_unique: number;
  }>;
  topic_similarities: Record<string, {
    common_topics: number;
    total_unique_topics: number;
    similarity_percentage: number;
    common_topic_list: string[];
  }>;
  summary: {
    companies_compared: number;
    total_problems_across_companies: number;
    most_similar_pair: [string, any];
    least_similar_pair: [string, any];
  };
  // Computed properties for backward compatibility
  companies: string[];
  metrics: {
    totalProblems: Record<string, number>;
    uniqueProblems: Record<string, number>;
    avgFrequency: Record<string, number>;
    difficultyDistribution: Record<string, {
      EASY: number;
      MEDIUM: number;
      HARD: number;
      UNKNOWN: number;
    }>;
    topTopics: Record<string, string[]>;
  };
  similarities: Array<{
    company1: string;
    company2: string;
    similarity: number;
    commonTopics: string[];
    sharedProblems: number;
  }>;
  recommendations: Array<{
    company: string;
    recommendation: string;
    reasoning: string;
  }>;
}

// FAANG companies for specialized analysis (using only companies available in dataset)
export const FAANG_COMPANIES = ['Google', 'Amazon', 'Meta', 'Microsoft'] as const;
export const MAJOR_TECH_COMPANIES = ['Google', 'Amazon', 'Meta', 'Microsoft'] as const;

export type FaangCompany = typeof FAANG_COMPANIES[number];
export type MajorTechCompany = typeof MAJOR_TECH_COMPANIES[number];

// Analytics dashboard configuration
export interface AnalyticsDashboardConfig {
  refreshInterval: number; // minutes
  maxCorrelationCompanies: number;
  defaultInsightLimit: number;
  cacheTimeout: number; // minutes
}

export const DEFAULT_ANALYTICS_CONFIG: AnalyticsDashboardConfig = {
  refreshInterval: 10,
  maxCorrelationCompanies: 10,
  defaultInsightLimit: 10,
  cacheTimeout: 5,
};

// Quality analytics types
export interface QualityDistributionData {
  originalityScore: number;
  totalVotes: number;
  count: number;
  category: 'hidden-gem' | 'rising-star' | 'interview-classic' | 'controversial' | 'standard';
}

export interface SentimentHeatmapData {
  topic: string;
  difficulty: 'EASY' | 'MEDIUM' | 'HARD' | 'UNKNOWN';
  avgOriginalityScore: number;
  avgLikes: number;
  avgDislikes: number;
  problemCount: number;
  sentiment: 'positive' | 'neutral' | 'negative';
}

export interface AcceptanceVsDifficultyData {
  title: string;
  acceptanceRate: number;
  perceivedDifficulty: number; // 1-3 scale (Easy=1, Medium=2, Hard=3)
  actualDifficulty: number; // Based on acceptance rate percentile
  originalityScore: number;
  totalVotes: number;
  category: string;
}

export interface QualityTrendData {
  timeframe: string;
  avgOriginalityScore: number;
  avgLikes: number;
  avgDislikes: number;
  newProblemsCount: number;
  qualityProblemsCount: number; // originality > 0.8
}

export interface HiddenGemsFilter {
  minOriginalityScore?: number;
  maxTotalVotes?: number;
  minLikes?: number;
  topics?: string[];
  difficulties?: ('EASY' | 'MEDIUM' | 'HARD')[];
  companies?: string[];
}

export interface QualityAnalyticsResponse {
  qualityDistribution: QualityDistributionData[];
  sentimentHeatmap: SentimentHeatmapData[];
  acceptanceVsDifficulty: AcceptanceVsDifficultyData[];
  qualityTrends: QualityTrendData[];
  hiddenGems: Array<{
    title: string;
    originalityScore: number;
    totalVotes: number;
    likes: number;
    topics: string[];
    difficulty: string;
    companies: string[];
  }>;
  risingStars: Array<{
    title: string;
    originalityScore: number;
    totalVotes: number;
    recentGrowth: number;
    topics: string[];
  }>;
  controversialProblems: Array<{
    title: string;
    originalityScore: number;
    likes: number;
    dislikes: number;
    controversyRatio: number;
    topics: string[];
  }>;
}