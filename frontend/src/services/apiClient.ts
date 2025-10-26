import type { StudyPlanRecommendationPayload, StudyPlanRecommendationResponse } from '../types';
import { config, logger } from '../config/environment';

// API Client with retry logic for 30+ second timeouts
export interface ApiResponse<T> {
  data: T;
  status: 'success' | 'error';
  message?: string;
  correlation_id?: string;
}

export interface ApiError {
  code: string;
  message: string;
  details?: string;
  correlation_id?: string;
}

export class ApiClientError extends Error {
  code: string;
  details?: string;
  correlation_id?: string;

  constructor(
    code: string,
    message: string,
    details?: string,
    correlation_id?: string
  ) {
    super(message);
    this.name = 'ApiClientError';
    this.code = code;
    this.details = details;
    this.correlation_id = correlation_id;
  }
}

interface RetryConfig {
  maxAttempts: number;
  baseDelay: number;
  maxDelay: number;
  timeout: number;
}

class ApiClient {
  private baseURL: string;
  private retryConfig: RetryConfig;

  constructor(baseURL?: string) {
    this.baseURL = baseURL || config.apiUrl;
    this.retryConfig = {
      maxAttempts: 3,
      baseDelay: 1000, // 1 second
      maxDelay: 10000, // 10 seconds
      timeout: config.apiTimeout, // Use configured timeout
    };
    
    logger.debug('ApiClient initialized', {
      baseURL: this.baseURL,
      timeout: this.retryConfig.timeout
    });
  }

  private async delay(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  private calculateRetryDelay(attempt: number): number {
    const exponentialDelay = this.retryConfig.baseDelay * Math.pow(2, attempt - 1);
    const jitter = Math.random() * 1000; // Add jitter to prevent thundering herd
    return Math.min(exponentialDelay + jitter, this.retryConfig.maxDelay);
  }

  private async fetchWithTimeout(url: string, options: RequestInit = {}): Promise<Response> {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), this.retryConfig.timeout);

    try {
      const response = await fetch(url, {
        ...options,
        signal: controller.signal,
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
          ...options.headers,
        },
      });
      
      clearTimeout(timeoutId);
      return response;
    } catch (error) {
      clearTimeout(timeoutId);
      if (error instanceof Error && error.name === 'AbortError') {
        throw new ApiClientError('TIMEOUT_ERROR', 'Request timed out after 45 seconds');
      }
      throw error;
    }
  }

  private async makeRequest<T>(
    endpoint: string,
    options: RequestInit = {},
    attempt: number = 1
  ): Promise<ApiResponse<T>> {
    const url = `${this.baseURL}${endpoint}`;
    
    try {
      logger.debug(`API Request (attempt ${attempt}): ${url}`);
      const startTime = Date.now();
      
      const response = await this.fetchWithTimeout(url, options);
      const responseTime = Date.now() - startTime;
      
      logger.debug(`API Response: ${response.status} (${responseTime}ms)`);

      if (!response.ok) {
        // Handle HTTP errors
        const errorMessage = `HTTP ${response.status}: ${response.statusText}`;
        let errorDetails = '';
        
        try {
          const errorBody = await response.text();
          if (errorBody) {
            errorDetails = errorBody;
          }
        } catch {
          // Ignore JSON parsing errors for error responses
        }

        // Determine if we should retry based on status code
        const shouldRetry = this.shouldRetry(response.status, attempt);
        
        if (shouldRetry) {
          const delay = this.calculateRetryDelay(attempt);
          logger.warn(`Retrying in ${delay}ms (attempt ${attempt + 1}/${this.retryConfig.maxAttempts})`);
          await this.delay(delay);
          return this.makeRequest<T>(endpoint, options, attempt + 1);
        }

        throw new ApiClientError(
          this.getErrorCode(response.status),
          errorMessage,
          errorDetails
        );
      }

      // Parse successful response
      const data = await response.json();
      return {
        data,
        status: 'success',
      };

    } catch (error) {
      // Handle network errors and other exceptions
      if (error instanceof ApiClientError) {
        throw error; // Re-throw our custom errors
      }

      const shouldRetry = attempt < this.retryConfig.maxAttempts;
      
      if (shouldRetry) {
        const delay = this.calculateRetryDelay(attempt);
        logger.warn(`Network error, retrying in ${delay}ms (attempt ${attempt + 1}/${this.retryConfig.maxAttempts})`);
        await this.delay(delay);
        return this.makeRequest<T>(endpoint, options, attempt + 1);
      }

      // Final attempt failed
      throw new ApiClientError(
        'NETWORK_ERROR',
        error instanceof Error ? error.message : 'Unknown network error',
        error instanceof Error ? error.stack : undefined
      );
    }
  }

  private shouldRetry(statusCode: number, attempt: number): boolean {
    if (attempt >= this.retryConfig.maxAttempts) {
      return false;
    }

    // Retry on server errors (5xx) and some client errors
    return statusCode >= 500 || statusCode === 429 || statusCode === 408;
  }

  private getErrorCode(statusCode: number): string {
    switch (statusCode) {
      case 400:
        return 'BAD_REQUEST';
      case 401:
        return 'UNAUTHORIZED';
      case 403:
        return 'FORBIDDEN';
      case 404:
        return 'NOT_FOUND';
      case 408:
        return 'REQUEST_TIMEOUT';
      case 429:
        return 'TOO_MANY_REQUESTS';
      case 500:
        return 'INTERNAL_SERVER_ERROR';
      case 502:
        return 'BAD_GATEWAY';
      case 503:
        return 'SERVICE_UNAVAILABLE';
      case 504:
        return 'GATEWAY_TIMEOUT';
      default:
        return 'HTTP_ERROR';
    }
  }

  // Public API methods
  async get<T>(endpoint: string, params?: Record<string, any>): Promise<ApiResponse<T>> {
    let url = endpoint;
    if (params) {
      const searchParams = new URLSearchParams();
      Object.entries(params).forEach(([key, value]) => {
        if (Array.isArray(value)) {
          // Handle arrays by adding multiple parameters with the same key
          value.forEach(item => searchParams.append(key, item.toString()));
        } else if (value !== undefined && value !== null) {
          searchParams.append(key, value.toString());
        }
      });
      const queryString = searchParams.toString();
      if (queryString) {
        url += (endpoint.includes('?') ? '&' : '?') + queryString;
      }
    }
    return this.makeRequest<T>(url, { method: 'GET' });
  }

  async post<T>(endpoint: string, data?: unknown): Promise<ApiResponse<T>> {
    return this.makeRequest<T>(endpoint, {
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  async put<T>(endpoint: string, data?: unknown): Promise<ApiResponse<T>> {
    return this.makeRequest<T>(endpoint, {
      method: 'PUT',
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  async delete<T>(endpoint: string): Promise<ApiResponse<T>> {
    return this.makeRequest<T>(endpoint, { method: 'DELETE' });
  }

  // Health check methods (these are working according to verification)
  async healthQuick() {
    return this.get<{ status: string; timestamp: string; version: string }>('/api/v1/health/quick');
  }

  async healthData() {
    return this.get<{
      data_available: boolean;
      sample_size: number;
      source_files: string[];
      cache_status: string;
      cache_stats: Record<string, unknown>;
      timestamp: string;
      status: string;
      message: string;
    }>('/api/v1/health/data');
  }

  // Company methods
  async getCompanyStats(params?: Record<string, any>) {
    return this.get<any>('/api/v1/companies/stats', params);
  }

  async getCompanyDetails(companyName: string) {
    return this.get<Record<string, unknown>>(`/api/v1/companies/${encodeURIComponent(companyName)}`);
  }

  // Topic methods (Phase 2)
  async getTopicTrends(limit: number = 25, params: Record<string, any> = {}) {
    return this.get<Record<string, unknown>>('/api/v1/topics/trends', { limit, ...params });
  }

  async getTopicFrequency(limit: number = 50) {
    return this.get<Record<string, unknown>>(`/api/v1/topics/frequency?limit=${limit}`);
  }

  async getTopicHeatmap(topTopics: number = 20, companies?: string[]) {
    return this.get<Record<string, unknown>>('/api/v1/topics/heatmap', {
      top_topics: topTopics,
      companies
    });
  }

  async getStudyPlanRecommendations(payload: StudyPlanRecommendationPayload) {
    return this.post<StudyPlanRecommendationResponse>('/api/v1/problems/recommendations', payload);
  }

  // Analytics methods (Phase 4)
  async getAnalyticsSummary(companies?: string[]) {
    const params: Record<string, any> = {};
    if (companies && companies.length > 0) {
      params.companies = companies;
    }
    return this.get<any>('/api/v1/analytics/summary', params);
  }

  async getAnalyticsInsights(companies?: string[], limit?: number) {
    const params: Record<string, any> = {};
    if (companies && companies.length > 0) {
      params.companies = companies;
    }
    if (limit) {
      params.limit = limit;
    }
    return this.get<any>('/api/v1/analytics/insights', params);
  }

  async getAnalyticsCorrelations(companies: string[], metric: string = 'composite') {
    return this.get<any>('/api/v1/analytics/correlations', { companies, metric });
  }

  async compareCompanies(companies: string[]) {
    return this.get<any>('/api/v1/companies/compare', { companies });
  }
}

// Create and export a singleton instance
export const apiClient = new ApiClient();

// Export the class for testing or custom instances
export { ApiClient };
