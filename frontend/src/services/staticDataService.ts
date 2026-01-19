/**
 * Static Data Service
 *
 * Loads pre-generated JSON data for static site deployment.
 * Replaces API calls with local file fetching.
 */

import type { CompanyData, ProblemData } from '../types/company';
import type { TopicTrend, TopicFrequency, TopicHeatmap } from '../types/topic';
import type { AnalyticsSummary } from '../types/analytics';

// Data manifest type
interface DataManifest {
  version: string;
  generated_at: string;
  total_companies: number;
  total_problems: number;
  total_records: number;
}

// Company detail data structure
interface CompanyDetailData {
  company: string;
  stats: {
    totalProblems: number;
    uniqueProblems: number;
    avgFrequency: number;
    avgAcceptanceRate: number;
    difficultyDistribution: {
      EASY: number;
      MEDIUM: number;
      HARD: number;
      UNKNOWN: number;
    };
  };
  problems: ProblemData[];
  topTopics: string[];
}

// Study plan types
interface StudyPlanDay {
  week: number;
  day: number;
  dayNumber: number;
  problems: {
    title: string;
    titleSlug: string;
    difficulty: string;
    topics: string[];
    link?: string;
  }[];
}

interface StudyPlan {
  id: string;
  name: string;
  description: string;
  durationWeeks: number;
  problemsPerDay: number;
  totalProblems: number;
  targetAudience: string;
  createdAt: string;
  days: StudyPlanDay[];
}

// All problems data (for client-side filtering)
interface AllProblemsData {
  title: string;
  titleSlug: string;
  difficulty: string;
  frequency?: number;
  acceptanceRate?: number;
  link?: string;
  topics: string[];
  companies: string[];
  companyCount: number;
  timeframes: string[];
}

// Problem preview data (from LeetCode metadata)
interface ProblemPreviewData {
  title: string;
  titleSlug: string;
  questionId?: string;
  difficulty: string;
  content_html?: string | null;
  content_text?: string | null;
  topic_tags: { name: string; slug: string }[];
  ac_rate?: number | null;
  likes?: number | null;
  dislikes?: number | null;
  is_paid_only: boolean;
  has_solution: boolean;
  has_video_solution: boolean;
}

class StaticDataService {
  private baseDataPath: string;
  private cache = new Map<string, unknown>();
  private manifest: DataManifest | null = null;

  constructor() {
    // Use Vite's BASE_URL for correct path in production
    this.baseDataPath = (import.meta.env.BASE_URL || '/') + 'data/';
  }

  /**
   * Load and cache JSON data from a path
   */
  async loadJSON<T>(path: string): Promise<T> {
    const cacheKey = path;

    if (this.cache.has(cacheKey)) {
      return this.cache.get(cacheKey) as T;
    }

    const url = this.baseDataPath + path;
    const response = await fetch(url);

    if (!response.ok) {
      throw new Error(`Failed to load ${url}: ${response.status} ${response.statusText}`);
    }

    const data = await response.json();
    this.cache.set(cacheKey, data);
    return data as T;
  }

  /**
   * Load the data manifest
   */
  async loadManifest(): Promise<DataManifest> {
    if (this.manifest) {
      return this.manifest;
    }
    this.manifest = await this.loadJSON<DataManifest>('index.json');
    return this.manifest;
  }

  /**
   * Load all company statistics
   */
  async loadCompanyStats(): Promise<CompanyData[]> {
    return this.loadJSON<CompanyData[]>('companies/stats.json');
  }

  /**
   * Load detailed data for a specific company
   */
  async loadCompanyData(companySlug: string): Promise<CompanyDetailData> {
    return this.loadJSON<CompanyDetailData>(`companies/${companySlug}.json`);
  }

  /**
   * Load topic trends data
   */
  async loadTopicTrends(): Promise<TopicTrend[]> {
    return this.loadJSON<TopicTrend[]>('topics/trends.json');
  }

  /**
   * Load topic frequency data
   */
  async loadTopicFrequency(): Promise<TopicFrequency[]> {
    return this.loadJSON<TopicFrequency[]>('topics/frequency.json');
  }

  /**
   * Load topic heatmap data
   */
  async loadTopicHeatmap(): Promise<TopicHeatmap> {
    return this.loadJSON<TopicHeatmap>('topics/heatmap.json');
  }

  /**
   * Load analytics summary
   */
  async loadAnalyticsSummary(): Promise<AnalyticsSummary> {
    return this.loadJSON<AnalyticsSummary>('analytics/summary.json');
  }

  /**
   * Load all problems for client-side filtering
   */
  async loadAllProblems(): Promise<AllProblemsData[]> {
    return this.loadJSON<AllProblemsData[]>('problems/all.json');
  }

  /**
   * Load problem previews (keyed by slug)
   */
  async loadProblemPreviews(): Promise<Record<string, ProblemPreviewData>> {
    return this.loadJSON<Record<string, ProblemPreviewData>>('problems/previews.json');
  }

  /**
   * Load a single problem preview by slug
   */
  async loadProblemPreview(slug: string): Promise<ProblemPreviewData | null> {
    const previews = await this.loadProblemPreviews();
    return previews[slug] || null;
  }

  /**
   * Load a pre-generated study plan
   */
  async loadStudyPlan(planId: string): Promise<StudyPlan> {
    return this.loadJSON<StudyPlan>(`study-plans/${planId}.json`);
  }

  /**
   * Get available study plan IDs
   */
  getAvailableStudyPlans(): { id: string; name: string }[] {
    return [
      { id: 'faang-4-weeks', name: 'FAANG Interview Prep (4 weeks)' },
      { id: 'beginner-2-weeks', name: 'Beginner Fundamentals (2 weeks)' },
      { id: 'advanced-3-weeks', name: 'Advanced Algorithms (3 weeks)' },
      { id: 'top-100-must-do', name: 'Top 100 Must-Do Problems' },
    ];
  }

  /**
   * Clear the cache (useful for development)
   */
  clearCache(): void {
    this.cache.clear();
    this.manifest = null;
  }

  /**
   * Check if static data is available
   */
  async isDataAvailable(): Promise<boolean> {
    try {
      await this.loadManifest();
      return true;
    } catch {
      return false;
    }
  }
}

// Export singleton instance
export const staticDataService = new StaticDataService();

// Export types
export type {
  DataManifest,
  CompanyDetailData,
  StudyPlan,
  StudyPlanDay,
  AllProblemsData,
  ProblemPreviewData,
};
