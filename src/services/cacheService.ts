import type { CompanyData, ProblemData } from '../types/company';

interface CacheItem<T> {
  data: T;
  timestamp: number;
  expiresAt: number;
}

export interface CachedCompanyProblems {
  problems: ProblemData[];
  total: number;
  offset: number;
  limit: number;
  hasMore?: boolean;
}

interface CacheConfig {
  defaultTTL: number; // Time to live in milliseconds
  maxSize: number; // Maximum number of items to cache
}

class CacheService {
  private config: CacheConfig = {
    defaultTTL: 60 * 60 * 1000, // 1 hour
    maxSize: 100
  };

  private getStorageKey(key: string): string {
    return `leetcode_cache_${key}`;
  }

  private isExpired(item: CacheItem<any>): boolean {
    return Date.now() > item.expiresAt;
  }

  private cleanupExpiredItems(): void {
    const keys = Object.keys(localStorage);
    const cacheKeys = keys.filter(key => key.startsWith('leetcode_cache_'));
    
    cacheKeys.forEach(key => {
      try {
        const item = JSON.parse(localStorage.getItem(key) || '');
        if (this.isExpired(item)) {
          localStorage.removeItem(key);
        }
      } catch (error) {
        // Remove corrupted cache items
        localStorage.removeItem(key);
      }
    });
  }

  private enforceMaxSize(): void {
    const keys = Object.keys(localStorage);
    const cacheKeys = keys.filter(key => key.startsWith('leetcode_cache_'));
    
    if (cacheKeys.length > this.config.maxSize) {
      // Sort by timestamp and remove oldest items
      const items = cacheKeys
        .map(key => {
          try {
            const item = JSON.parse(localStorage.getItem(key) || '');
            return { key, timestamp: item.timestamp };
          } catch {
            return { key, timestamp: 0 };
          }
        })
        .sort((a, b) => a.timestamp - b.timestamp);

      const itemsToRemove = items.slice(0, items.length - this.config.maxSize);
      itemsToRemove.forEach(item => localStorage.removeItem(item.key));
    }
  }

  set<T>(key: string, data: T, ttl?: number): void {
    try {
      const expirationTime = ttl || this.config.defaultTTL;
      const cacheItem: CacheItem<T> = {
        data,
        timestamp: Date.now(),
        expiresAt: Date.now() + expirationTime
      };

      localStorage.setItem(this.getStorageKey(key), JSON.stringify(cacheItem));
      
      // Periodic cleanup
      if (Math.random() < 0.1) { // 10% chance to trigger cleanup
        this.cleanupExpiredItems();
        this.enforceMaxSize();
      }
    } catch (error) {
      console.warn('Failed to cache data:', error);
    }
  }

  get<T>(key: string): T | null {
    try {
      const cached = localStorage.getItem(this.getStorageKey(key));
      if (!cached) return null;

      const item: CacheItem<T> = JSON.parse(cached);
      
      if (this.isExpired(item)) {
        localStorage.removeItem(this.getStorageKey(key));
        return null;
      }

      return item.data;
    } catch (error) {
      console.warn('Failed to retrieve cached data:', error);
      localStorage.removeItem(this.getStorageKey(key));
      return null;
    }
  }

  remove(key: string): void {
    localStorage.removeItem(this.getStorageKey(key));
  }

  clear(): void {
    const keys = Object.keys(localStorage);
    const cacheKeys = keys.filter(key => key.startsWith('leetcode_cache_'));
    cacheKeys.forEach(key => localStorage.removeItem(key));
  }

  // Company-specific cache methods
  setCompanyStats(data: CompanyData[]): void {
    this.set('company_stats', data, 30 * 60 * 1000); // 30 minutes
  }

  getCompanyStats(): CompanyData[] | null {
    return this.get<CompanyData[]>('company_stats');
  }

  setCompanyDetail(companyName: string, data: CompanyData): void {
    this.set(`company_detail_${companyName.toLowerCase()}`, data, 60 * 60 * 1000); // 1 hour
  }

  getCompanyDetail(companyName: string): CompanyData | null {
    return this.get<CompanyData>(`company_detail_${companyName.toLowerCase()}`);
  }

  private getCompanyProblemsKey(companyName: string, topicKey?: string): string {
    return `company_problems_${companyName.toLowerCase()}_${topicKey ?? 'all'}`;
  }

  setCompanyProblems(companyName: string, data: CachedCompanyProblems, topic?: string): void {
    const key = this.getCompanyProblemsKey(companyName, topic ? topic.toLowerCase() : undefined);
    this.set(key, data, 60 * 60 * 1000); // 1 hour
  }

  getCompanyProblems(companyName: string, topic?: string): CachedCompanyProblems | null {
    const key = this.getCompanyProblemsKey(companyName, topic ? topic.toLowerCase() : undefined);
    return this.get<CachedCompanyProblems>(key);
  }

  // Health check cache
  setHealthStatus(data: any): void {
    this.set('health_status', data, 5 * 60 * 1000); // 5 minutes
  }

  getHealthStatus(): any | null {
    return this.get('health_status');
  }

  // Cache statistics
  getCacheStats(): { totalItems: number; totalSize: number } {
    const keys = Object.keys(localStorage);
    const cacheKeys = keys.filter(key => key.startsWith('leetcode_cache_'));
    
    let totalSize = 0;
    cacheKeys.forEach(key => {
      const item = localStorage.getItem(key);
      if (item) {
        totalSize += item.length;
      }
    });

    return {
      totalItems: cacheKeys.length,
      totalSize
    };
  }
}

// Export singleton instance
export const cacheService = new CacheService();
