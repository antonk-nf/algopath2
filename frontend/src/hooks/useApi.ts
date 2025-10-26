import { useState, useEffect, useCallback } from 'react';
import { apiClient, ApiClientError } from '../services/apiClient';
import type { ApiResponse } from '../services/apiClient';
import { useAppContext } from './useAppContext';

interface UseApiState<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
}

export function useApi<T>(
  endpoint: string,
  immediate: boolean = true
): UseApiState<T> {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { dispatch } = useAppContext();

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    
    // Update global loading state
    dispatch({
      type: 'SET_LOADING',
      payload: { key: endpoint, loading: true }
    });

    try {
      const response: ApiResponse<T> = await apiClient.get<T>(endpoint);
      setData(response.data);
      
      // Clear any previous errors
      dispatch({
        type: 'SET_ERROR',
        payload: { key: endpoint, error: null }
      });
      
    } catch (err) {
      const errorMessage = err instanceof ApiClientError 
        ? `${err.code}: ${err.message}` 
        : 'An unexpected error occurred';
      
      setError(errorMessage);
      
      // Update global error state
      dispatch({
        type: 'SET_ERROR',
        payload: { key: endpoint, error: errorMessage }
      });
      
      console.error(`API Error for ${endpoint}:`, err);
    } finally {
      setLoading(false);
      
      // Update global loading state
      dispatch({
        type: 'SET_LOADING',
        payload: { key: endpoint, loading: false }
      });
    }
  }, [endpoint, dispatch]);

  useEffect(() => {
    if (immediate) {
      fetchData();
    }
  }, [fetchData, immediate]);

  return {
    data,
    loading,
    error,
    refetch: fetchData,
  };
}

// Specialized hook for health checks
export function useHealthCheck() {
  const { data, loading, error, refetch } = useApi<{
    status: string;
    timestamp: string;
    version: string;
  }>('/api/v1/health/quick');

  const { dispatch } = useAppContext();

  useEffect(() => {
    if (data) {
      dispatch({
        type: 'SET_API_HEALTH',
        payload: {
          status: data.status === 'healthy' ? 'healthy' : 'degraded',
          lastCheck: data.timestamp,
          endpointStatus: {
            'health/quick': 'working'
          }
        }
      });
    } else if (error) {
      dispatch({
        type: 'SET_API_HEALTH',
        payload: {
          status: 'unhealthy',
          lastCheck: new Date().toISOString(),
          endpointStatus: {
            'health/quick': 'error'
          }
        }
      });
    }
  }, [data, error, dispatch]);

  return { data, loading, error, refetch };
}

// Hook for company stats (currently failing according to verification)
export function useCompanyStats() {
  return useApi<Record<string, unknown>[]>('/api/v1/companies/stats', false); // Don't fetch immediately
}