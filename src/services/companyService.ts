import { apiClient } from './apiClient';
import { cacheService, type CachedCompanyProblems } from './cacheService';
import { staticDataService, type CompanyDetailData } from './staticDataService';
import { filterProblems, paginateArray } from '../utils/clientFiltering';
import type { CompanyData, ProblemData, CompanyStats } from '../types/company';

interface CompanyProblemsOptions {
  limit?: number;
  offset?: number;
  topic?: string | null;
  forceRemote?: boolean;
}

interface CompanyProblemsResult {
  problems: ProblemData[];
  total: number;
  limit: number;
  offset: number;
  hasMore: boolean;
  nextOffset?: number | null;
}

// Check if running in static mode (no API server)
const isStaticMode = (): boolean => {
  // Check for explicit static mode flag
  if (import.meta.env.VITE_STATIC_MODE === 'true') {
    return true;
  }
  // In production builds, use static mode by default
  if (import.meta.env.PROD) {
    return true;
  }
  return false;
};

// Cache for loaded company data in static mode
const staticCompanyDataCache = new Map<string, CompanyDetailData>();

export class CompanyService {
  // Get all company statistics
  async getCompanyStats(): Promise<CompanyData[]> {
    // Use static data in static mode
    if (isStaticMode()) {
      try {
        const stats = await staticDataService.loadCompanyStats();
        cacheService.setCompanyStats(stats);
        return stats;
      } catch (error) {
        console.warn('Failed to load static company stats, falling back to cache/mock:', error);
      }
    }

    // Try to get from cache first
    const cachedData = cacheService.getCompanyStats();
    if (cachedData && cachedData.length >= 100) {
      console.log('Returning cached company stats');
      return cachedData;
    }

    if (cachedData) {
      cacheService.remove('company_stats');
    }

    try {
      const aggregated: CompanyData[] = [];
      let page = 1;
      const pageSize = 200;
      let iterations = 0;

      while (true) {
        const response = await apiClient.getCompanyStats({ page, page_size: pageSize });
        const payload = response.data;
        const normalizedPage = this.transformCompanyStatsResponse(payload);
        if (normalizedPage.length === 0) {
          break;
        }
        aggregated.push(...normalizedPage);

        const { hasNext, totalPages } = this.extractPaginationInfo(payload);
        iterations += 1;
        if (!hasNext || (totalPages && page >= totalPages) || iterations > 10) {
          break;
        }
        page += 1;
      }

      const dedupedMap = new Map<string, CompanyData>();
      aggregated.forEach(company => {
        if (!dedupedMap.has(company.company)) {
          dedupedMap.set(company.company, company);
        }
      });

      const normalizedData = Array.from(dedupedMap.values());

      if (normalizedData.length === 0) {
        console.warn('API returned empty or invalid company data, using mock data');
        const mockData = this.getMockCompanyData();
        cacheService.setCompanyStats(mockData);
        return mockData;
      }

      cacheService.setCompanyStats(normalizedData);
      return normalizedData;
    } catch (error) {
      console.error('Failed to fetch company stats:', error);
      
      // Return mock data for development/demo purposes when API fails
      const mockData = this.getMockCompanyData();
      cacheService.setCompanyStats(mockData);
      return mockData;
    }
  }

  private extractPaginationInfo(payload: any): { hasNext: boolean; totalPages?: number } {
    if (!payload || Array.isArray(payload)) {
      return { hasNext: false };
    }

    const currentPage = typeof payload.page === 'number'
      ? payload.page
      : typeof payload.current_page === 'number'
        ? payload.current_page
        : undefined;

    const totalPagesRaw = payload.total_pages ?? payload.totalPages;
    const totalPages = typeof totalPagesRaw === 'number' ? totalPagesRaw : undefined;

    let hasNext = Boolean(payload.has_next ?? payload.hasNext);
    if (totalPages && currentPage) {
      hasNext = currentPage < totalPages;
    }

    return { hasNext, totalPages };
  }

  private transformCompanyStatsResponse(apiPayload: any): CompanyData[] {
    if (Array.isArray(apiPayload)) {
      return this.normalizeCompanyStatsArray(apiPayload);
    }

    if (apiPayload && Array.isArray(apiPayload.data)) {
      return this.normalizeCompanyStatsArray(apiPayload.data);
    }

    return [];
  }

  private normalizeCompanyStatsArray(items: any[]): CompanyData[] {
    return items
      .map(item => this.normalizeCompanyStatsItem(item))
      .filter((entry): entry is CompanyData => entry !== null);
  }

  private normalizeCompanyStatsItem(raw: any): CompanyData | null {
    if (!raw) {
      return null;
    }

    const companyName = String(raw.company || raw.company_name || '').trim();
    if (!companyName) {
      return null;
    }

    const toNumber = (value: unknown, fallback = 0): number => {
      const parsed = typeof value === 'string' ? Number(value) : value;
      return Number.isFinite(parsed as number) ? Number(parsed) : fallback;
    };

    const difficultyRaw = raw.difficulty_distribution || raw.difficultyDistribution || {};
    const difficultyDistribution = {
      EASY: toNumber(difficultyRaw.EASY ?? difficultyRaw.easy, 0),
      MEDIUM: toNumber(difficultyRaw.MEDIUM ?? difficultyRaw.medium, 0),
      HARD: toNumber(difficultyRaw.HARD ?? difficultyRaw.hard, 0),
      UNKNOWN: toNumber(difficultyRaw.UNKNOWN ?? difficultyRaw.unknown, 0)
    };

    const topTopicsRaw = raw.top_topics ?? raw.topTopics ?? [];
    let topTopics: string[] = [];
    if (Array.isArray(topTopicsRaw)) {
      topTopics = topTopicsRaw.map(topic => String(topic));
    } else if (typeof topTopicsRaw === 'string') {
      topTopics = topTopicsRaw.split(',').map(topic => topic.trim()).filter(Boolean);
    } else if (topTopicsRaw && typeof topTopicsRaw === 'object') {
      topTopics = Object.entries(topTopicsRaw)
        .sort((a, b) => Number(b[1]) - Number(a[1]))
        .map(([topic]) => String(topic));
    }

    const timeframeRaw = raw.timeframe_coverage ?? raw.timeframeCoverage ?? [];
    const timeframeCoverage = Array.isArray(timeframeRaw)
      ? timeframeRaw.map(value => String(value))
      : [];

    const totalProblems = toNumber(raw.total_problems ?? raw.totalProblems, 0);
    const uniqueProblems = toNumber(raw.unique_problems ?? raw.uniqueProblems, 0);
    const avgFrequency = toNumber(raw.avg_frequency ?? raw.avgFrequency, 0);
    const avgAcceptanceRate = toNumber(raw.avg_acceptance_rate ?? raw.avgAcceptanceRate, 0);
    const rankValue = raw.rank !== undefined ? toNumber(raw.rank, 0) : undefined;

    return {
      company: companyName,
      totalProblems,
      uniqueProblems,
      avgFrequency,
      avgAcceptanceRate,
      difficultyDistribution,
      topTopics,
      timeframeCoverage,
      rank: rankValue
    };
  }

  // Mock data for development/demo when API is not available
  private getMockCompanyData(): CompanyData[] {
    return [
      {
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
        topTopics: ['Arrays', 'Dynamic Programming', 'Trees', 'Graphs', 'Strings'],
        timeframeCoverage: ['30d', '3m', '6m'],
        rank: 1
      },
      {
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
        topTopics: ['Arrays', 'Trees', 'Dynamic Programming', 'Strings', 'Graphs'],
        timeframeCoverage: ['30d', '3m'],
        rank: 2
      },
      {
        company: 'Microsoft',
        totalProblems: 130,
        uniqueProblems: 105,
        avgFrequency: 2.3,
        avgAcceptanceRate: 0.62,
        difficultyDistribution: {
          EASY: 35,
          MEDIUM: 65,
          HARD: 30,
          UNKNOWN: 0
        },
        topTopics: ['Arrays', 'Strings', 'Dynamic Programming', 'Trees', 'Hash Tables'],
        timeframeCoverage: ['30d', '3m', '6m'],
        rank: 3
      },
      {
        company: 'Meta',
        totalProblems: 125,
        uniqueProblems: 100,
        avgFrequency: 2.7,
        avgAcceptanceRate: 0.60,
        difficultyDistribution: {
          EASY: 20,
          MEDIUM: 75,
          HARD: 30,
          UNKNOWN: 0
        },
        topTopics: ['Arrays', 'Hash Tables', 'Trees', 'Dynamic Programming', 'Graphs'],
        timeframeCoverage: ['30d', '3m'],
        rank: 4
      },
      {
        company: 'Apple',
        totalProblems: 95,
        uniqueProblems: 80,
        avgFrequency: 2.1,
        avgAcceptanceRate: 0.68,
        difficultyDistribution: {
          EASY: 25,
          MEDIUM: 50,
          HARD: 20,
          UNKNOWN: 0
        },
        topTopics: ['Arrays', 'Strings', 'Trees', 'Dynamic Programming', 'Math'],
        timeframeCoverage: ['30d', '3m'],
        rank: 5
      },
      {
        company: 'Netflix',
        totalProblems: 85,
        uniqueProblems: 70,
        avgFrequency: 1.9,
        avgAcceptanceRate: 0.55,
        difficultyDistribution: {
          EASY: 15,
          MEDIUM: 45,
          HARD: 25,
          UNKNOWN: 0
        },
        topTopics: ['Arrays', 'Strings', 'Dynamic Programming', 'System Design', 'Graphs'],
        timeframeCoverage: ['30d', '3m'],
        rank: 6
      }
    ];
  }

  // Get details for a specific company
  async getCompanyDetails(companyName: string): Promise<CompanyData> {
    // Use static data in static mode
    if (isStaticMode()) {
      try {
        const slug = this.toSlug(companyName);
        let companyData = staticCompanyDataCache.get(slug);

        if (!companyData) {
          companyData = await staticDataService.loadCompanyData(slug);
          staticCompanyDataCache.set(slug, companyData);
        }

        const result: CompanyData = {
          company: companyData.company,
          totalProblems: companyData.stats.totalProblems,
          uniqueProblems: companyData.stats.uniqueProblems,
          avgFrequency: companyData.stats.avgFrequency,
          avgAcceptanceRate: companyData.stats.avgAcceptanceRate,
          difficultyDistribution: companyData.stats.difficultyDistribution,
          topTopics: companyData.topTopics,
          timeframeCoverage: [],
        };

        cacheService.setCompanyDetail(companyName, result);
        return result;
      } catch (error) {
        console.warn(`Failed to load static company details for ${companyName}:`, error);
      }
    }

    // Try to get from cache first
    const cachedData = cacheService.getCompanyDetail(companyName);
    if (cachedData) {
      console.log(`Returning cached company details for ${companyName}`);
      return cachedData;
    }

    try {
      const response = await apiClient.getCompanyDetails(companyName);
      const apiData = response.data as any;
      
      // Transform API response to match frontend CompanyData interface
      const transformedData: CompanyData = this.transformApiResponseToCompanyData(apiData, companyName);

      // Cache top problems from the details payload if available
      const topProblemsRaw = Array.isArray(apiData?.top_problems)
        ? apiData.top_problems
        : Array.isArray(apiData?.company_stats?.top_problems)
          ? apiData.company_stats.top_problems
          : null;

      if (Array.isArray(topProblemsRaw) && topProblemsRaw.length > 0) {
        const normalizedTopProblems = topProblemsRaw
          .map((item: any) => this.normalizeCompanyProblem({ ...item, company: companyName }, companyName))
          .filter((problem): problem is ProblemData => problem !== null);

        if (normalizedTopProblems.length > 0) {
          const cachedPayload: CachedCompanyProblems = {
            problems: normalizedTopProblems,
            total: normalizedTopProblems.length,
            offset: 0,
            limit: normalizedTopProblems.length,
            hasMore: false
          };
          cacheService.setCompanyProblems(companyName, cachedPayload);
        }
      }
      
      // Cache the transformed response
      cacheService.setCompanyDetail(companyName, transformedData);
      return transformedData;
    } catch (error) {
      console.error(`Failed to fetch details for company ${companyName}:`, error);
      
      // Return mock data for the requested company if available
      const mockData = this.getMockCompanyData();
      const mockCompany = mockData.find(c => c.company.toLowerCase() === companyName.toLowerCase());
      
      if (mockCompany) {
        // Cache the mock data too
        cacheService.setCompanyDetail(companyName, mockCompany);
        return mockCompany;
      }
      
      // If no mock data available, throw the error
      throw error;
    }
  }

  // Transform API response to match frontend CompanyData interface
  private transformApiResponseToCompanyData(apiData: any, companyName: string): CompanyData {
    // Handle case where API returns the expected format directly
    if (apiData.company && apiData.difficultyDistribution) {
      return apiData as CompanyData;
    }

    // Handle case where API returns nested structure
    const stats = apiData.company_stats || apiData;
    
    // Transform difficulty distribution from API format to frontend format
    const apiDifficultyDist = stats.difficulty_distribution || {};
    const difficultyDistribution = {
      EASY: apiDifficultyDist.Easy || apiDifficultyDist.EASY || 0,
      MEDIUM: apiDifficultyDist.Medium || apiDifficultyDist.MEDIUM || 0,
      HARD: apiDifficultyDist.Hard || apiDifficultyDist.HARD || 0,
      UNKNOWN: apiDifficultyDist.Unknown || apiDifficultyDist.UNKNOWN || 0
    };

    // Transform top topics from API format
    let topTopics: string[] = [];
    if (stats.top_topics) {
      if (Array.isArray(stats.top_topics)) {
        topTopics = stats.top_topics;
      } else if (typeof stats.top_topics === 'object') {
        // If it's an object with topic counts, get the keys
        topTopics = Object.keys(stats.top_topics);
      }
    }

    // Transform timeframes
    const timeframeCoverage = stats.timeframes_available || stats.timeframeCoverage || ['30d'];

    return {
      company: stats.company || companyName,
      totalProblems: stats.total_problems || stats.totalProblems || 0,
      uniqueProblems: stats.unique_problems || stats.uniqueProblems || 0,
      avgFrequency: stats.avg_frequency || stats.avgFrequency || 0,
      avgAcceptanceRate: stats.avg_acceptance_rate || stats.avgAcceptanceRate || 0,
      difficultyDistribution,
      topTopics: topTopics.slice(0, 10), // Limit to top 10
      timeframeCoverage,
      rank: stats.rank
    };
  }

  // Convert company name to URL-safe slug
  private toSlug(name: string): string {
    return name.toLowerCase().trim().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
  }

  // Get problems for a specific company
  async getCompanyProblems(
    companyName: string,
    options: CompanyProblemsOptions = {}
  ): Promise<CompanyProblemsResult> {
    const { limit = 25, offset = 0, topic = null, forceRemote = false } = options;
    const normalizedTopic = topic ? topic.trim() : null;

    // Use static data in static mode
    if (isStaticMode()) {
      try {
        const slug = this.toSlug(companyName);
        let companyData = staticCompanyDataCache.get(slug);

        if (!companyData) {
          companyData = await staticDataService.loadCompanyData(slug);
          staticCompanyDataCache.set(slug, companyData);
        }

        // Filter problems if topic is specified
        let problems = companyData.problems.map(p => ({
          ...p,
          company: companyName
        })) as ProblemData[];

        if (normalizedTopic) {
          problems = filterProblems(problems, { topic: normalizedTopic });
        }

        // Paginate
        const page = Math.floor(offset / limit) + 1;
        const paginated = paginateArray(problems, page, limit);

        return {
          problems: paginated.data,
          total: paginated.total,
          limit,
          offset,
          hasMore: paginated.hasNext,
          nextOffset: paginated.hasNext ? offset + limit : null,
        };
      } catch (error) {
        console.warn(`Failed to load static problems for ${companyName}:`, error);
      }
    }

    if (!forceRemote && offset === 0) {
      const cached = cacheService.getCompanyProblems(companyName, normalizedTopic || undefined);
      if (cached) {
        console.log(
          `Returning cached problems for ${companyName}${normalizedTopic ? ` (topic: ${normalizedTopic})` : ''}`
        );
        return {
          problems: cached.problems,
          total: cached.total,
          limit: cached.limit,
          offset: cached.offset,
          hasMore: cached.hasMore ?? cached.problems.length < cached.total,
          nextOffset: cached.offset + cached.problems.length
        };
      }
    }

    try {
      const params: Record<string, any> = {
        limit,
        offset
      };
      if (normalizedTopic) {
        params.topic = normalizedTopic;
      }
      const response = await apiClient.get(`/api/v1/companies/${encodeURIComponent(companyName)}/problems`, params);
      const normalized = this.transformCompanyProblemsResponse(
        response.data,
        companyName,
        { limit, offset }
      );

      if (!forceRemote && offset === 0) {
        cacheService.setCompanyProblems(
          companyName,
          {
            problems: normalized.problems,
            total: normalized.total,
            limit: normalized.limit,
            offset: normalized.offset,
            hasMore: normalized.hasMore
          },
          normalizedTopic || undefined
        );
      }

      return normalized;
    } catch (error) {
      console.error(`Failed to fetch problems for company ${companyName}:`, error);

      const mockProblems = this.getMockProblemsData(companyName);
      const fallback: CompanyProblemsResult = {
        problems: mockProblems,
        total: mockProblems.length,
        limit,
        offset,
        hasMore: false,
        nextOffset: null
      };

      if (offset === 0 && mockProblems.length > 0) {
        cacheService.setCompanyProblems(
          companyName,
          {
            problems: mockProblems,
            total: mockProblems.length,
            limit,
            offset: 0,
            hasMore: false
          },
          normalizedTopic || undefined
        );
      }

      return fallback;
    }
  }

  private transformCompanyProblemsResponse(
    apiPayload: any,
    fallbackCompany: string,
    request: { limit: number; offset: number }
  ): CompanyProblemsResult {
    if (!apiPayload) {
      return {
        problems: [],
        total: 0,
        limit: request.limit,
        offset: request.offset,
        hasMore: false,
        nextOffset: null
      };
    }

    const payloadRoot = apiPayload.data ?? apiPayload;
    const items: any[] = Array.isArray(payloadRoot?.problems)
      ? payloadRoot.problems as any[]
      : Array.isArray(payloadRoot)
        ? payloadRoot as any[]
        : [];

    const problems = items
      .map((item: any) => this.normalizeCompanyProblem(item, fallbackCompany))
      .filter((problem): problem is ProblemData => problem !== null);

    const total = typeof payloadRoot?.total === 'number'
      ? payloadRoot.total
      : problems.length;

    const nextOffset = typeof payloadRoot?.next_offset === 'number'
      ? payloadRoot.next_offset
      : request.offset + problems.length;

    const hasMore = typeof payloadRoot?.has_more === 'boolean'
      ? payloadRoot.has_more
      : nextOffset < total;

    const limit = typeof payloadRoot?.limit === 'number'
      ? payloadRoot.limit
      : request.limit;

    const offset = typeof payloadRoot?.offset === 'number'
      ? payloadRoot.offset
      : request.offset;

    return {
      problems,
      total,
      limit,
      offset,
      hasMore,
      nextOffset: hasMore ? nextOffset : null
    };
  }

  private normalizeCompanyProblem(raw: any, fallbackCompany: string): ProblemData | null {
    if (!raw) {
      return null;
    }

    const toNumber = (value: unknown): number | undefined => {
      if (value === null || value === undefined) {
        return undefined;
      }
      const parsed = typeof value === 'string' ? Number(value) : value;
      return Number.isFinite(parsed as number) ? Number(parsed) : undefined;
    };

    const title = String(raw.title || raw.problem_title || '').trim();
    if (!title) {
      return null;
    }

    const topicsRaw = raw.topics || raw.topic_list || [];
    const topics = Array.isArray(topicsRaw)
      ? topicsRaw.map((topic: any) => String(topic))
      : typeof topicsRaw === 'string'
        ? topicsRaw.split(',').map((topic: string) => topic.trim()).filter(Boolean)
        : [];

    const difficulty = String(raw.difficulty || raw.problem_difficulty || 'UNKNOWN').toUpperCase();

    const acceptanceValue = raw.acceptance_rate ?? raw.acceptanceRate;
    const normalizedAcceptance = (() => {
      const numeric = toNumber(acceptanceValue);
      if (numeric === undefined) return undefined;
      return numeric > 1 ? numeric / 100 : numeric;
    })();

    const frequencyValue = (() => {
      const candidates = [
        raw.frequency,
        raw.company_frequency,
        raw.frequency_score,
        raw.frequency_value,
        raw.avg_frequency,
        raw.frequencyAvg,
        raw.freq,
        raw.frequency_count,
        raw.frequencyCount,
        raw.total_frequency,
        raw.totalFrequency
      ];
      for (const candidate of candidates) {
        const numeric = toNumber(candidate);
        if (numeric !== undefined) {
          return numeric;
        }
      }
      return undefined;
    })();

    return {
      title,
      titleSlug: raw.title_slug || raw.titleSlug,
      difficulty: ['EASY', 'MEDIUM', 'HARD', 'UNKNOWN'].includes(difficulty)
        ? (difficulty as ProblemData['difficulty'])
        : 'UNKNOWN',
      frequency: frequencyValue,
      acceptanceRate: normalizedAcceptance,
      link: raw.link || raw.url || raw.leetcode_link,
      topics,
      company: raw.company || raw.company_name || fallbackCompany,
      timeframe: raw.timeframe,
      totalFrequency: toNumber(raw.total_frequency ?? raw.totalFrequency),
      companyCount: toNumber(raw.company_count ?? raw.companyCount ?? raw.total_companies),
      likes: toNumber(raw.likes),
      dislikes: toNumber(raw.dislikes),
      originalityScore: toNumber(raw.originality_score),
      totalVotes: toNumber(raw.total_votes),
      hasOfficialSolution: raw.has_official_solution ?? raw.hasOfficialSolution ?? undefined,
      hasVideoSolution: raw.has_video_solution ?? raw.hasVideoSolution ?? undefined,
      isPaidOnly: raw.is_paid_only ?? raw.isPaidOnly ?? undefined,
      qualityTier: raw.quality_tier || raw.qualityTier || undefined
    };
  }

  // Mock problems data for development
  private getMockProblemsData(companyName: string): ProblemData[] {
    const baseProblems: Omit<ProblemData, 'company'>[] = [
      {
        title: 'Two Sum',
        difficulty: 'EASY',
        companyCount: 470,
        frequency: 3.4,
        link: 'https://leetcode.com/problems/two-sum/',
        topics: ['Array', 'Hash Table'],
        timeframe: '30d'
      },
      {
        title: 'Add Two Numbers',
        difficulty: 'MEDIUM',
        companyCount: 430,
        frequency: 2.7,
        link: 'https://leetcode.com/problems/add-two-numbers/',
        topics: ['Linked List', 'Math', 'Recursion'],
        timeframe: '30d'
      },
      {
        title: 'Longest Substring Without Repeating Characters',
        difficulty: 'MEDIUM',
        companyCount: 410,
        frequency: 2.1,
        link: 'https://leetcode.com/problems/longest-substring-without-repeating-characters/',
        topics: ['Hash Table', 'String', 'Sliding Window'],
        timeframe: '30d'
      },
      {
        title: 'Median of Two Sorted Arrays',
        difficulty: 'HARD',
        companyCount: 220,
        frequency: 1.4,
        link: 'https://leetcode.com/problems/median-of-two-sorted-arrays/',
        topics: ['Array', 'Binary Search', 'Divide and Conquer'],
        timeframe: '3m'
      },
      {
        title: 'Longest Palindromic Substring',
        difficulty: 'MEDIUM',
        companyCount: 360,
        frequency: 2.0,
        link: 'https://leetcode.com/problems/longest-palindromic-substring/',
        topics: ['String', 'Dynamic Programming'],
        timeframe: '30d'
      }
    ];

    return baseProblems.map(problem => ({
      ...problem,
      company: companyName
    }));
  }

  // Filter and sort companies based on criteria
  filterCompanies(companies: CompanyData[], criteria: {
    searchQuery?: string;
    difficulties?: ('EASY' | 'MEDIUM' | 'HARD')[];
    minProblems?: number;
    maxProblems?: number;
    sortBy?: 'company' | 'totalProblems' | 'avgFrequency' | 'rank';
    sortOrder?: 'asc' | 'desc';
  }): CompanyData[] {
    let filtered = [...companies];

    // Apply search filter
    if (criteria.searchQuery) {
      const query = criteria.searchQuery.toLowerCase();
      filtered = filtered.filter(company =>
        company.company.toLowerCase().includes(query)
      );
    }

    // Apply problem count filters
    if (criteria.minProblems !== undefined) {
      filtered = filtered.filter(company => company.totalProblems >= criteria.minProblems!);
    }

    if (criteria.maxProblems !== undefined) {
      filtered = filtered.filter(company => company.totalProblems <= criteria.maxProblems!);
    }

    // Apply difficulty filters (if company has problems in selected difficulties)
    if (criteria.difficulties && criteria.difficulties.length > 0) {
      filtered = filtered.filter(company => {
        return criteria.difficulties!.some(difficulty => 
          company.difficultyDistribution[difficulty] > 0
        );
      });
    }

    // Apply sorting
    if (criteria.sortBy) {
      filtered.sort((a, b) => {
        let aValue: number | string;
        let bValue: number | string;

        switch (criteria.sortBy) {
          case 'company':
            aValue = a.company.toLowerCase();
            bValue = b.company.toLowerCase();
            break;
          case 'totalProblems':
            aValue = a.totalProblems;
            bValue = b.totalProblems;
            break;
          case 'avgFrequency':
            aValue = a.avgFrequency;
            bValue = b.avgFrequency;
            break;
          case 'rank':
            aValue = a.rank || 999999;
            bValue = b.rank || 999999;
            break;
          default:
            return 0;
        }

        if (typeof aValue === 'string' && typeof bValue === 'string') {
          const comparison = aValue.localeCompare(bValue);
          return criteria.sortOrder === 'desc' ? -comparison : comparison;
        } else {
          const comparison = (aValue as number) - (bValue as number);
          return criteria.sortOrder === 'desc' ? -comparison : comparison;
        }
      });
    }

    return filtered;
  }

  // Calculate summary statistics
  calculateStats(companies: CompanyData[]): CompanyStats {
    if (companies.length === 0) {
      return {
        totalCompanies: 0,
        totalProblems: 0,
        avgProblemsPerCompany: 0,
        topCompanies: []
      };
    }

    const totalProblems = companies.reduce((sum, company) => sum + company.totalProblems, 0);
    const avgProblemsPerCompany = totalProblems / companies.length;

    // Get top 10 companies by total problems
    const topCompanies = [...companies]
      .sort((a, b) => b.totalProblems - a.totalProblems)
      .slice(0, 10);

    return {
      totalCompanies: companies.length,
      totalProblems,
      avgProblemsPerCompany: Math.round(avgProblemsPerCompany * 100) / 100,
      topCompanies
    };
  }

  calculateUniqueTopics(companies: CompanyData[]): number {
    const topics = new Set<string>();
    companies.forEach(company => {
      company.topTopics?.forEach(topic => {
        if (topic) {
          topics.add(topic);
        }
      });
    });
    return topics.size;
  }

  calculateTimeframeCoverage(companies: CompanyData[]): number {
    const timeframes = new Set<string>();
    companies.forEach(company => {
      company.timeframeCoverage?.forEach(tf => {
        if (tf) {
          timeframes.add(tf);
        }
      });
    });
    return timeframes.size;
  }
}

// Export singleton instance
export const companyService = new CompanyService();
