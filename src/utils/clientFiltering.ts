/**
 * Client-side filtering and pagination utilities
 *
 * Used for static site deployment where all data is loaded at once
 * and filtering/pagination happens in the browser.
 */

import type { ProblemData, CompanyData } from '../types/company';

// Pagination result type
export interface PaginatedResult<T> {
  data: T[];
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
  hasNext: boolean;
  hasPrev: boolean;
}

// Problem filter options
export interface ProblemFilters {
  topic?: string | null;
  difficulty?: string | null;
  timeframe?: string | null;
  search?: string | null;
  minFrequency?: number;
  maxFrequency?: number;
}

// Company filter options
export interface CompanyFilters {
  search?: string | null;
  difficulties?: string[];
  minProblems?: number;
  maxProblems?: number;
}

// Sort options
export interface SortOptions<T> {
  field: keyof T;
  order: 'asc' | 'desc';
}

/**
 * Paginate an array of items
 */
export function paginateArray<T>(
  items: T[],
  page: number,
  pageSize: number
): PaginatedResult<T> {
  const total = items.length;
  const totalPages = Math.ceil(total / pageSize);
  const safePage = Math.max(1, Math.min(page, totalPages || 1));
  const startIndex = (safePage - 1) * pageSize;
  const endIndex = startIndex + pageSize;
  const data = items.slice(startIndex, endIndex);

  return {
    data,
    total,
    page: safePage,
    pageSize,
    totalPages,
    hasNext: safePage < totalPages,
    hasPrev: safePage > 1,
  };
}

/**
 * Filter problems by various criteria
 */
export function filterProblems(
  problems: ProblemData[],
  filters: ProblemFilters
): ProblemData[] {
  let filtered = [...problems];

  // Filter by topic
  if (filters.topic) {
    const topic = filters.topic.toLowerCase();
    filtered = filtered.filter((p) =>
      p.topics?.some((t) => t.toLowerCase() === topic)
    );
  }

  // Filter by difficulty
  if (filters.difficulty) {
    const difficulty = filters.difficulty.toUpperCase();
    filtered = filtered.filter((p) => p.difficulty === difficulty);
  }

  // Filter by timeframe
  if (filters.timeframe) {
    filtered = filtered.filter((p) => p.timeframe === filters.timeframe);
  }

  // Filter by search term (title)
  if (filters.search) {
    const search = filters.search.toLowerCase();
    filtered = filtered.filter((p) => p.title.toLowerCase().includes(search));
  }

  // Filter by frequency range
  if (filters.minFrequency !== undefined) {
    filtered = filtered.filter(
      (p) => (p.frequency ?? 0) >= filters.minFrequency!
    );
  }

  if (filters.maxFrequency !== undefined) {
    filtered = filtered.filter(
      (p) => (p.frequency ?? 0) <= filters.maxFrequency!
    );
  }

  return filtered;
}

/**
 * Filter companies by various criteria
 */
export function filterCompanies(
  companies: CompanyData[],
  filters: CompanyFilters
): CompanyData[] {
  let filtered = [...companies];

  // Filter by search term (company name)
  if (filters.search) {
    const search = filters.search.toLowerCase();
    filtered = filtered.filter((c) => c.company.toLowerCase().includes(search));
  }

  // Filter by difficulty availability
  if (filters.difficulties && filters.difficulties.length > 0) {
    filtered = filtered.filter((c) =>
      filters.difficulties!.some((d) => {
        const key = d.toUpperCase() as keyof typeof c.difficultyDistribution;
        return (c.difficultyDistribution[key] ?? 0) > 0;
      })
    );
  }

  // Filter by problem count range
  if (filters.minProblems !== undefined) {
    filtered = filtered.filter((c) => c.totalProblems >= filters.minProblems!);
  }

  if (filters.maxProblems !== undefined) {
    filtered = filtered.filter((c) => c.totalProblems <= filters.maxProblems!);
  }

  return filtered;
}

/**
 * Sort an array of items by a field
 */
export function sortArray<T>(
  items: T[],
  field: keyof T,
  order: 'asc' | 'desc' = 'desc'
): T[] {
  return [...items].sort((a, b) => {
    const aVal = a[field];
    const bVal = b[field];

    // Handle nullish values
    if (aVal == null && bVal == null) return 0;
    if (aVal == null) return order === 'asc' ? 1 : -1;
    if (bVal == null) return order === 'asc' ? -1 : 1;

    // String comparison
    if (typeof aVal === 'string' && typeof bVal === 'string') {
      const comparison = aVal.localeCompare(bVal);
      return order === 'asc' ? comparison : -comparison;
    }

    // Number comparison
    const numA = Number(aVal);
    const numB = Number(bVal);
    const comparison = numA - numB;
    return order === 'asc' ? comparison : -comparison;
  });
}

/**
 * Extract unique topics from problems
 */
export function extractUniqueTopics(problems: ProblemData[]): string[] {
  const topics = new Set<string>();
  problems.forEach((p) => {
    p.topics?.forEach((t) => {
      if (t) topics.add(t);
    });
  });
  return Array.from(topics).sort();
}

/**
 * Extract unique difficulties from problems
 */
export function extractUniqueDifficulties(
  problems: ProblemData[]
): string[] {
  const difficulties = new Set<string>();
  problems.forEach((p) => {
    if (p.difficulty) difficulties.add(p.difficulty);
  });
  return Array.from(difficulties).sort();
}

/**
 * Extract unique timeframes from problems
 */
export function extractUniqueTimeframes(problems: ProblemData[]): string[] {
  const timeframes = new Set<string>();
  problems.forEach((p) => {
    if (p.timeframe) timeframes.add(p.timeframe);
  });
  return Array.from(timeframes);
}

/**
 * Search problems by title (fuzzy match)
 */
export function searchProblems(
  problems: ProblemData[],
  query: string
): ProblemData[] {
  if (!query || query.trim() === '') {
    return problems;
  }

  const lowerQuery = query.toLowerCase().trim();
  const words = lowerQuery.split(/\s+/);

  return problems.filter((p) => {
    const title = p.title.toLowerCase();
    // All words must be present in the title
    return words.every((word) => title.includes(word));
  });
}

/**
 * Group problems by a field
 */
export function groupProblemsBy<K extends keyof ProblemData>(
  problems: ProblemData[],
  field: K
): Map<ProblemData[K], ProblemData[]> {
  const groups = new Map<ProblemData[K], ProblemData[]>();

  problems.forEach((p) => {
    const key = p[field];
    if (key == null) return;

    if (!groups.has(key)) {
      groups.set(key, []);
    }
    groups.get(key)!.push(p);
  });

  return groups;
}

/**
 * Calculate statistics for a set of problems
 */
export function calculateProblemStats(problems: ProblemData[]): {
  total: number;
  byDifficulty: Record<string, number>;
  avgFrequency: number;
  avgAcceptanceRate: number;
  topTopics: { topic: string; count: number }[];
} {
  const byDifficulty: Record<string, number> = {
    EASY: 0,
    MEDIUM: 0,
    HARD: 0,
    UNKNOWN: 0,
  };

  const topicCounts: Record<string, number> = {};
  let totalFrequency = 0;
  let totalAcceptance = 0;
  let freqCount = 0;
  let accCount = 0;

  problems.forEach((p) => {
    byDifficulty[p.difficulty] = (byDifficulty[p.difficulty] ?? 0) + 1;

    p.topics?.forEach((t) => {
      topicCounts[t] = (topicCounts[t] ?? 0) + 1;
    });

    if (p.frequency != null) {
      totalFrequency += p.frequency;
      freqCount++;
    }

    if (p.acceptanceRate != null) {
      totalAcceptance += p.acceptanceRate;
      accCount++;
    }
  });

  const topTopics = Object.entries(topicCounts)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 10)
    .map(([topic, count]) => ({ topic, count }));

  return {
    total: problems.length,
    byDifficulty,
    avgFrequency: freqCount > 0 ? totalFrequency / freqCount : 0,
    avgAcceptanceRate: accCount > 0 ? totalAcceptance / accCount : 0,
    topTopics,
  };
}
