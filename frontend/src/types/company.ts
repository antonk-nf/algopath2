// Company data types based on the design document

export interface CompanyData {
  company: string;
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
  topTopics: string[];
  timeframeCoverage: string[];
  rank?: number;
}

export interface ProblemData {
  title: string;
  titleSlug?: string;
  difficulty: 'EASY' | 'MEDIUM' | 'HARD' | 'UNKNOWN';
  frequency?: number;
  acceptanceRate?: number;
  link?: string;
  topics: string[];
  company: string;
  timeframe?: string;
  totalFrequency?: number;
  companyCount?: number;
  // Quality metrics from LeetCode metadata
  likes?: number;
  dislikes?: number;
  originalityScore?: number; // likes/(likes+dislikes)
  totalVotes?: number; // likes+dislikes (proxy for problem age/exposure)
  hasOfficialSolution?: boolean;
  hasVideoSolution?: boolean;
  isPaidOnly?: boolean;
  qualityTier?: 'hidden-gem' | 'rising-star' | 'interview-classic' | 'controversial' | 'standard';
}

export interface ProblemQualityMetrics {
  likes: number;
  dislikes: number;
  originalityScore: number;
  totalVotes: number;
  qualityPercentile: number;
  ageCategory: 'new' | 'established' | 'classic';
  sentimentCategory: 'loved' | 'mixed' | 'controversial';
}

export interface CompanyFilterCriteria {
  searchQuery?: string;
  difficulties?: ('EASY' | 'MEDIUM' | 'HARD')[];
  minProblems?: number;
  maxProblems?: number;
  sortBy?: 'company' | 'totalProblems' | 'avgFrequency' | 'rank';
  sortOrder?: 'asc' | 'desc';
}

export interface CompanyStats {
  totalCompanies: number;
  totalProblems: number;
  avgProblemsPerCompany: number;
  topCompanies: CompanyData[];
}
