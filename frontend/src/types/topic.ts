export interface TopicTrend {
  topic: string;
  trendDirection?: string;
  trendStrength?: number;
  trendStrengthAbs?: number;
  totalFrequency?: number;
  timeframeFrequencies?: Record<string, number>;
  shareByTimeframe?: Record<string, number>;
  additionalData?: Record<string, unknown>;
  validTimeframeCount?: number;
  timeframeCount?: number;
  sufficientData?: boolean;
}

export interface TopicFrequency {
  topic: string;
  frequency: number;
  companies?: string[];
  timeframes?: Record<string, number>;
  additionalData?: Record<string, unknown>;
}

export interface TopicHeatmap {
  topics: string[];
  companies: string[];
  matrix: number[][];
  timeframes?: string[];
  topicTotals?: number[];
  companyTotals?: number[];
  metadata?: Record<string, unknown>;
}
