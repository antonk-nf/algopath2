import { useEffect, useState, useCallback } from 'react';
import { topicService } from '../services/topicService';
import type { TopicTrend, TopicFrequency, TopicHeatmap } from '../types/topic';

interface UseTopicDataResult {
  trends: TopicTrend[];
  trendsLoading: boolean;
  trendsError: string | null;
  refreshTrends: () => Promise<void>;
  frequencyData: TopicFrequency[];
  frequencyAvailable: boolean;
  frequencyError: string | null;
  heatmapData: TopicHeatmap | null;
  heatmapAvailable: boolean;
  heatmapError: string | null;
}

export function useTopicData(limit: number = 20): UseTopicDataResult {
  const [trends, setTrends] = useState<TopicTrend[]>([]);
  const [trendsLoading, setTrendsLoading] = useState<boolean>(false);
  const [trendsError, setTrendsError] = useState<string | null>(null);

  const [frequencyData, setFrequencyData] = useState<TopicFrequency[]>([]);
  const [frequencyAvailable, setFrequencyAvailable] = useState<boolean>(false);
  const [frequencyError, setFrequencyError] = useState<string | null>(null);

  const [heatmapData, setHeatmapData] = useState<TopicHeatmap | null>(null);
  const [heatmapAvailable, setHeatmapAvailable] = useState<boolean>(false);
  const [heatmapError, setHeatmapError] = useState<string | null>(null);

  const loadTrends = useCallback(async () => {
    setTrendsLoading(true);
    setTrendsError(null);

    try {
      const data = await topicService.getTopicTrends(limit);
      setTrends(data);
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to load topic trends';
      setTrendsError(message);
      setTrends([]);
    } finally {
      setTrendsLoading(false);
    }
  }, [limit]);

  const loadFrequency = useCallback(async () => {
    try {
      const data = await topicService.getTopicFrequency(limit);
      setFrequencyData(data);
      setFrequencyAvailable(data.length > 0);
      setFrequencyError(null);
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Topic frequency analysis is currently unavailable';
      setFrequencyError(message);
      setFrequencyAvailable(false);
      setFrequencyData([]);
    }
  }, [limit]);

  const loadHeatmap = useCallback(async () => {
    try {
      const data = await topicService.getTopicHeatmap(limit);
      // Validate matrix data before marking as available
      if (data && data.topics?.length && data.companies?.length && Array.isArray(data.matrix)) {
        setHeatmapData(data);
        setHeatmapAvailable(true);
        setHeatmapError(null);
      } else {
        throw new Error('Incomplete heatmap data');
      }
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Topic heatmap is currently unavailable';
      setHeatmapError(message);
      setHeatmapAvailable(false);
      setHeatmapData(null);
    }
  }, [limit]);

  useEffect(() => {
    loadTrends();
    loadFrequency();
    loadHeatmap();
  }, [loadTrends, loadFrequency, loadHeatmap]);

  return {
    trends,
    trendsLoading,
    trendsError,
    refreshTrends: loadTrends,
    frequencyData,
    frequencyAvailable,
    frequencyError,
    heatmapData,
    heatmapAvailable,
    heatmapError,
  };
}
