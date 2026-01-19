import { apiClient, ApiClientError } from './apiClient';
import { cacheService } from './cacheService';
import { staticDataService } from './staticDataService';
import type { TopicTrend, TopicFrequency, TopicHeatmap } from '../types/topic';

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

class TopicService {
  private trendsCacheKey = 'topic_trends';

  async getTopicTrends(
    limit: number = 25,
    options?: { sortByAbs?: boolean; sortOrder?: 'asc' | 'desc'; disableCache?: boolean }
  ): Promise<TopicTrend[]> {
    const { sortByAbs = false, sortOrder, disableCache = false } = options || {};

    // Use static data in static mode
    if (isStaticMode()) {
      try {
        let trends = await staticDataService.loadTopicTrends();

        // Apply sorting if requested
        if (sortByAbs) {
          trends = [...trends].sort((a, b) => {
            const absA = Math.abs(a.trendStrength ?? 0);
            const absB = Math.abs(b.trendStrength ?? 0);
            return sortOrder === 'asc' ? absA - absB : absB - absA;
          });
        } else if (sortOrder) {
          trends = [...trends].sort((a, b) => {
            const valA = a.trendStrength ?? 0;
            const valB = b.trendStrength ?? 0;
            return sortOrder === 'asc' ? valA - valB : valB - valA;
          });
        }

        return trends.slice(0, limit);
      } catch (error) {
        console.warn('Failed to load static topic trends:', error);
      }
    }

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
    // Use static data in static mode
    if (isStaticMode()) {
      try {
        const frequencies = await staticDataService.loadTopicFrequency();
        return frequencies.slice(0, limit);
      } catch (error) {
        console.warn('Failed to load static topic frequency:', error);
      }
    }

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
    // Use static data in static mode
    if (isStaticMode()) {
      try {
        // If specific companies are requested, compute heatmap client-side
        if (companies && companies.length > 0) {
          return await this.computeHeatmapClientSide(topTopics, companies);
        }

        // Otherwise use pre-generated heatmap for top companies
        const heatmap = await staticDataService.loadTopicHeatmap();
        // Limit topics if requested
        if (topTopics && topTopics < heatmap.topics.length) {
          return {
            ...heatmap,
            topics: heatmap.topics.slice(0, topTopics),
            matrix: heatmap.matrix.slice(0, topTopics),
            topicTotals: heatmap.topicTotals?.slice(0, topTopics),
          };
        }
        return heatmap;
      } catch (error) {
        console.warn('Failed to load static topic heatmap:', error);
      }
    }

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

  /**
   * Compute heatmap data client-side from all problems data.
   * Used when specific companies are requested that may not be in the pre-generated heatmap.
   */
  private async computeHeatmapClientSide(topTopics: number, companies: string[]): Promise<TopicHeatmap> {
    const allProblems = await staticDataService.loadAllProblems();

    // Count topic frequencies across all problems for selected companies
    const topicCounts: Record<string, number> = {};
    const topicCompanyCounts: Record<string, Record<string, number>> = {};

    for (const problem of allProblems) {
      // Check if problem belongs to any of the selected companies
      const matchingCompanies = problem.companies.filter(c => companies.includes(c));
      if (matchingCompanies.length === 0) continue;

      for (const topic of problem.topics) {
        // Track total topic count
        topicCounts[topic] = (topicCounts[topic] || 0) + 1;

        // Track per-company counts
        if (!topicCompanyCounts[topic]) {
          topicCompanyCounts[topic] = {};
        }
        for (const company of matchingCompanies) {
          topicCompanyCounts[topic][company] = (topicCompanyCounts[topic][company] || 0) + 1;
        }
      }
    }

    // Get top topics by total count
    const sortedTopics = Object.entries(topicCounts)
      .sort((a, b) => b[1] - a[1])
      .slice(0, topTopics)
      .map(([topic]) => topic);

    // Build the matrix: rows = topics, columns = companies
    const matrix: number[][] = sortedTopics.map(topic => {
      return companies.map(company => {
        return topicCompanyCounts[topic]?.[company] || 0;
      });
    });

    // Calculate totals
    const topicTotals = sortedTopics.map(topic => topicCounts[topic] || 0);
    const companyTotals = companies.map(company => {
      return sortedTopics.reduce((sum, topic) => {
        return sum + (topicCompanyCounts[topic]?.[company] || 0);
      }, 0);
    });

    return {
      topics: sortedTopics,
      companies: companies,
      matrix,
      topicTotals,
      companyTotals,
    };
  }
}

export const topicService = new TopicService();
