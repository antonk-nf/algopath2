import { apiClient, ApiClientError } from './apiClient';
import { cacheService } from './cacheService';
import type { TopicTrend, TopicFrequency, TopicHeatmap } from '../types/topic';

class TopicService {
  private trendsCacheKey = 'topic_trends';

  async getTopicTrends(
    limit: number = 25,
    options?: { sortByAbs?: boolean; sortOrder?: 'asc' | 'desc'; disableCache?: boolean }
  ): Promise<TopicTrend[]> {
    const { sortByAbs = false, sortOrder, disableCache = false } = options || {};
    const canUseCache = typeof window !== 'undefined' && typeof localStorage !== 'undefined';
    const allowCache = canUseCache && !sortByAbs && !disableCache && (!sortOrder || sortOrder === 'desc');

    if (allowCache) {
      const cached = cacheService.get<TopicTrend[]>(this.trendsCacheKey);
      if (cached) {
        return cached;
      }
    }

    try {
      const params: Record<string, any> = {};
      if (sortByAbs) {
        params.sort_by_abs = true;
      }
      if (sortOrder) {
        params.sort_order = sortOrder;
      }

      const response = await apiClient.getTopicTrends(limit, params);
      const payload = response.data as any;
      const items: any[] = Array.isArray(payload?.data)
        ? payload.data
        : Array.isArray(payload)
        ? payload
        : [];

      const trends: TopicTrend[] = items.map((item) => ({
        topic: item.topic || item.name || 'Unknown Topic',
        trendDirection: item.trend_direction || item.trendDirection || item.direction,
        trendStrength: typeof item.trend_strength === 'number'
          ? item.trend_strength
          : typeof item.trendStrength === 'number'
          ? item.trendStrength
          : typeof item.trend_score === 'number'
          ? item.trend_score
          : undefined,
        trendStrengthAbs: typeof item.trend_strength_abs === 'number'
          ? item.trend_strength_abs
          : undefined,
        totalFrequency: typeof item.total_frequency === 'number'
          ? item.total_frequency
          : typeof item.frequency === 'number'
          ? item.frequency
          : undefined,
        timeframeFrequencies: item.timeframe_frequencies || item.timeframeFrequencies || {},
        shareByTimeframe: item.share_by_timeframe || item.shareByTimeframe || {},
        sufficientData: typeof item.sufficient_data === 'boolean'
          ? item.sufficient_data
          : item.sufficientData,
        timeframeCount: typeof item.timeframe_count === 'number'
          ? item.timeframe_count
          : item.timeframeCount,
        validTimeframeCount: typeof item.valid_timeframe_count === 'number'
          ? item.valid_timeframe_count
          : item.validTimeframeCount,
        additionalData: item
      }));

      if (allowCache && trends.length > 0) {
        cacheService.set(this.trendsCacheKey, trends, 10 * 60 * 1000);
      }

      return trends;
    } catch (error) {
      const message = error instanceof ApiClientError ? error.message : 'Failed to fetch topic trends';
      throw new Error(message);
    }
  }

  async getTopicFrequency(limit: number = 50): Promise<TopicFrequency[]> {
    try {
      const response = await apiClient.getTopicFrequency(limit);
      const payload = response.data as any;
      const items: any[] = Array.isArray(payload?.data)
        ? payload.data
        : Array.isArray(payload)
        ? payload
        : [];

      if (items.length === 0) {
        throw new Error('No frequency data available');
      }

      return items.map((item) => ({
        topic: item.topic || item.name || 'Unknown Topic',
        frequency: typeof item.frequency === 'number' ? item.frequency : Number(item.frequency) || 0,
        companies: Array.isArray(item.companies) ? item.companies : undefined,
        timeframes: item.timeframes || item.timeframe_breakdown,
        additionalData: item
      }));
    } catch (error) {
      const message = error instanceof ApiClientError ? error.message : 'Topic frequency endpoint unavailable';
      throw new Error(message);
    }
  }

  async getTopicHeatmap(topTopics: number = 20, companies?: string[]): Promise<TopicHeatmap> {
    try {
      const response = await apiClient.getTopicHeatmap(topTopics, companies);
      const payload = response.data as any;

      if (!payload || !Array.isArray(payload.topics) || !Array.isArray(payload.companies)) {
        throw new Error('Invalid heatmap data');
      }

      const rawMatrix = Array.isArray(payload.matrix) ? payload.matrix : [];
      const matrix: number[][] = rawMatrix.map((row: any) =>
        Array.isArray(row) ? row.map((value) => Number(value) || 0) : []
      );

      return {
        topics: payload.topics,
        companies: payload.companies,
        matrix,
        topicTotals: Array.isArray(payload.topic_totals)
          ? payload.topic_totals.map((value: any) => Number(value) || 0)
          : undefined,
        companyTotals: Array.isArray(payload.company_totals)
          ? payload.company_totals.map((value: any) => Number(value) || 0)
          : undefined,
        timeframes: Array.isArray(payload.metadata?.timeframes) ? payload.metadata.timeframes : undefined,
        metadata: payload.metadata
      };
    } catch (error) {
      const message = error instanceof ApiClientError ? error.message : 'Topic heatmap endpoint unavailable';
      throw new Error(message);
    }
  }
}

export const topicService = new TopicService();
