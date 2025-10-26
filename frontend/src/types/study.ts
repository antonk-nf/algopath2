// Study Plan types based on the design document

export interface StudyPlan {
  id: string;
  name: string;
  targetCompanies: string[];
  duration: number; // weeks
  dailyGoal: number; // problems per day
  focusAreas: string[];
  schedule: StudySession[];
  progress: StudyProgress;
  createdAt: string;
  updatedAt: string;
}

export interface StudySession {
  id: string;
  date: string; // ISO date string
  problems: StudyProblem[];
  completed: boolean;
  completedAt?: string;
}

export interface StudyProblem {
  title: string;
  difficulty: 'EASY' | 'MEDIUM' | 'HARD' | 'UNKNOWN';
  topics: string[];
  company: string;
  link?: string;
  status: 'not_started' | 'in_progress' | 'completed' | 'skipped';
  completedAt?: string;
  notes?: string;
  // Quality metrics
  qualityScore?: number;
  originalityScore?: number;
  likes?: number;
  dislikes?: number;
  totalVotes?: number;
  acceptanceRate?: number;
  qualityTier?: 'Premium' | 'High' | 'Good' | 'Average' | 'Unknown';
  recommendationReason?: string;
  isHiddenGem?: boolean;
  isInterviewClassic?: boolean;
}

export interface StudyProgress {
  totalProblems: number;
  completedProblems: number;
  skippedProblems: number;
  currentStreak: number;
  longestStreak: number;
  averageProblemsPerDay: number;
  completionRate: number; // percentage
  difficultyBreakdown: {
    EASY: { completed: number; total: number };
    MEDIUM: { completed: number; total: number };
    HARD: { completed: number; total: number };
  };
  topicProgress: Record<string, { completed: number; total: number }>;
  companyProgress: Record<string, { completed: number; total: number }>;
}

export interface StudyPlanFormData {
  name: string;
  targetCompanies: string[];
  duration: number; // weeks
  dailyGoal: number; // problems per day
  skillLevel: 'beginner' | 'intermediate' | 'advanced';
  focusAreas: string[];
  startDate: string; // ISO date string
  // Quality-aware options
  learningMode?: 'balanced' | 'interview_classics' | 'hidden_gems' | 'adaptive';
  qualityPreference?: 'quality_first' | 'popularity_first' | 'balanced' | 'discovery';
  adaptiveDifficulty?: boolean;
  includeQualityMetrics?: boolean;
}

export interface StudyPlanGeneratorOptions {
  prioritizeDifficulty?: ('EASY' | 'MEDIUM' | 'HARD')[];
  includeTopics?: string[];
  excludeTopics?: string[];
  maxProblemsPerCompany?: number;
  balanceAcrossCompanies?: boolean;
  // Quality-based options
  learningMode?: 'balanced' | 'interview_classics' | 'hidden_gems' | 'adaptive';
  qualityPreference?: 'quality_first' | 'popularity_first' | 'balanced' | 'discovery';
  minQualityScore?: number;
  adaptiveDifficulty?: boolean;
  includeQualityMetrics?: boolean;
}

export interface StudyPlanRecommendationPayload {
  companies?: string[];
  focus_topics?: string[];
  skill_level: 'beginner' | 'intermediate' | 'advanced';
  duration_weeks: number;
  daily_goal: number;
  balance_companies?: boolean;
  max_per_company?: number | null;
}

export interface RecommendedProblemSummary {
  title: string;
  difficulty?: string;
  topics: string[];
  acceptance_rate?: number;
  frequency?: number;
  companies: string[];
  recommended_company?: string;
  link?: string;
}

export interface StudyPlanRecommendationResponse {
  recommendations: RecommendedProblemSummary[];
  requested_count: number;
  selected_count: number;
  available_pool: number;
  skill_level: 'beginner' | 'intermediate' | 'advanced';
  filters: Record<string, unknown>;
}
