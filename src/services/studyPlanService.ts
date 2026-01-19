import type { 
  StudyPlan, 
  StudyPlanFormData, 
  StudyPlanGeneratorOptions,
  StudySession,
  StudyProblem,
  StudyProgress,
  ProblemData,
  CompanyData 
} from '../types';

class StudyPlanService {
  private readonly STORAGE_KEY = 'interview_prep_study_plans';
  private readonly BACKUP_KEY = 'interview_prep_backup';
  private readonly EXPORT_KEY = 'interview_prep_export_reminder';


  // Generate a study plan based on form data
  generateStudyPlan(
    formData: StudyPlanFormData,
    availableProblems: ProblemData[],
    _companyData: CompanyData[],
    options: StudyPlanGeneratorOptions = {}
  ): StudyPlan {
    const {
      prioritizeDifficulty = ['EASY', 'MEDIUM', 'HARD'],
      balanceAcrossCompanies = true,
      maxProblemsPerCompany = 50,
      learningMode = 'balanced',
      qualityPreference = 'balanced',
      minQualityScore = 0.0,
      adaptiveDifficulty = true,
      includeQualityMetrics = true
    } = options;

    // Filter problems by target companies
    const relevantProblems = availableProblems.filter(problem =>
      formData.targetCompanies.includes(problem.company)
    );

    // Apply quality filtering if enabled
    const qualityFilteredProblems = includeQualityMetrics 
      ? this.applyQualityFiltering(relevantProblems, minQualityScore, learningMode)
      : relevantProblems;

    // Sort problems by priority (frequency, difficulty, quality, etc.)
    const sortedProblems = this.prioritizeProblemsWithQuality(
      qualityFilteredProblems,
      formData.skillLevel,
      prioritizeDifficulty,
      learningMode,
      qualityPreference
    );

    // Calculate total problems needed
    const totalProblems = formData.duration * 7 * formData.dailyGoal;
    
    // Select problems for the study plan with quality awareness
    const selectedProblems = this.selectQualityAwareProblems(
      sortedProblems,
      totalProblems,
      formData.targetCompanies,
      formData.skillLevel,
      learningMode,
      balanceAcrossCompanies,
      maxProblemsPerCompany,
      adaptiveDifficulty
    );

    // Generate adaptive schedule if enabled
    const schedule = adaptiveDifficulty 
      ? this.generateAdaptiveSchedule(
          selectedProblems,
          formData.startDate,
          formData.duration,
          formData.dailyGoal,
          formData.skillLevel
        )
      : this.generateSchedule(
          selectedProblems,
          formData.startDate,
          formData.duration,
          formData.dailyGoal
        );

    // Create study plan
    const studyPlan: StudyPlan = {
      id: this.generateId(),
      name: formData.name,
      targetCompanies: formData.targetCompanies,
      duration: formData.duration,
      dailyGoal: formData.dailyGoal,
      focusAreas: formData.focusAreas,
      schedule,
      progress: this.initializeProgress(selectedProblems),
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString()
    };

    return studyPlan;
  }

  // Apply quality filtering based on learning mode
  private applyQualityFiltering(
    problems: ProblemData[],
    minQualityScore: number,
    learningMode: string
  ): ProblemData[] {
    return problems.filter(problem => {
      // Basic quality score check
      const qualityScore = this.calculateQualityScore(problem);
      if (qualityScore < minQualityScore) return false;

      // Mode-specific filtering
      switch (learningMode) {
        case 'interview_classics':
          return this.isInterviewClassic(problem);
        case 'hidden_gems':
          return this.isHiddenGem(problem);
        case 'adaptive':
        case 'balanced':
        default:
          return true; // Include all problems that meet basic quality threshold
      }
    });
  }

  // Calculate composite quality score for a problem
  private calculateQualityScore(problem: ProblemData): number {
    const originalityScore = (problem as any).originalityScore || 0.5;
    const likes = (problem as any).likes || 0;
    const totalVotes = (problem as any).totalVotes || 1;
    const acceptanceRate = problem.acceptanceRate || 0.5;

    // Normalize likes (assuming max ~10k likes for popular problems)
    const normalizedLikes = Math.min(likes / 10000, 1);
    
    // Composite score considering multiple factors
    return (
      originalityScore * 0.4 +
      normalizedLikes * 0.3 +
      acceptanceRate * 0.2 +
      (totalVotes > 100 ? 0.1 : 0) // Bonus for established problems
    );
  }

  // Check if problem is an interview classic
  private isInterviewClassic(problem: ProblemData): boolean {
    const likes = (problem as any).likes || 0;
    const originalityScore = (problem as any).originalityScore || 0;
    const totalVotes = (problem as any).totalVotes || 0;
    
    return likes >= 1000 && originalityScore >= 0.75 && totalVotes >= 2000;
  }

  // Check if problem is a hidden gem
  private isHiddenGem(problem: ProblemData): boolean {
    const originalityScore = (problem as any).originalityScore || 0;
    const totalVotes = (problem as any).totalVotes || 0;
    const likes = (problem as any).likes || 0;
    
    return originalityScore >= 0.85 && totalVotes <= 2000 && likes >= 50;
  }

  // Enhanced prioritization with quality metrics
  private prioritizeProblemsWithQuality(
    problems: ProblemData[],
    skillLevel: 'beginner' | 'intermediate' | 'advanced',
    prioritizeDifficulty: ('EASY' | 'MEDIUM' | 'HARD')[],
    learningMode: string,
    qualityPreference: string
  ): ProblemData[] {
    return problems.sort((a, b) => {
      // First, sort by difficulty preference based on skill level
      const difficultyWeight = this.getDifficultyWeight(a.difficulty, b.difficulty, skillLevel, prioritizeDifficulty);
      if (difficultyWeight !== 0) return difficultyWeight;

      // Apply quality-based sorting
      const qualityWeightA = this.getQualityWeight(a, learningMode, qualityPreference);
      const qualityWeightB = this.getQualityWeight(b, learningMode, qualityPreference);
      if (qualityWeightB !== qualityWeightA) {
        return qualityWeightB - qualityWeightA;
      }

      // Then by frequency (higher frequency first)
      const freqA = typeof a.frequency === 'number' ? a.frequency : 0;
      const freqB = typeof b.frequency === 'number' ? b.frequency : 0;
      if (freqB !== freqA) {
        return freqB - freqA;
      }

      // Finally by acceptance rate (adaptive based on skill level)
      const accA = typeof a.acceptanceRate === 'number' ? a.acceptanceRate : 0.5;
      const accB = typeof b.acceptanceRate === 'number' ? b.acceptanceRate : 0.5;
      if (skillLevel === 'beginner') {
        return accB - accA; // Higher acceptance rate for beginners
      } else {
        return accA - accB; // Lower acceptance rate for advanced (more challenging)
      }
    });
  }

  // Calculate quality weight based on learning mode and preference
  private getQualityWeight(
    problem: ProblemData,
    learningMode: string,
    qualityPreference: string
  ): number {
    const qualityScore = this.calculateQualityScore(problem);
    const isClassic = this.isInterviewClassic(problem);
    const isGem = this.isHiddenGem(problem);
    const likes = (problem as any).likes || 0;
    const originalityScore = (problem as any).originalityScore || 0.5;

    let weight = qualityScore;

    // Adjust weight based on learning mode
    switch (learningMode) {
      case 'interview_classics':
        weight += isClassic ? 0.5 : 0;
        weight += Math.min(likes / 5000, 0.3); // Bonus for popular problems
        break;
      case 'hidden_gems':
        weight += isGem ? 0.5 : 0;
        weight += originalityScore * 0.3; // Bonus for high originality
        break;
      case 'adaptive':
        weight += (isClassic ? 0.2 : 0) + (isGem ? 0.3 : 0); // Balanced approach
        break;
      case 'balanced':
      default:
        weight += (isClassic ? 0.1 : 0) + (isGem ? 0.1 : 0); // Slight preference
        break;
    }

    // Adjust weight based on quality preference
    switch (qualityPreference) {
      case 'quality_first':
        weight += originalityScore * 0.4;
        break;
      case 'popularity_first':
        weight += Math.min(likes / 10000, 0.4);
        break;
      case 'discovery':
        weight += isGem ? 0.4 : 0;
        break;
      case 'balanced':
      default:
        // Already balanced in base calculation
        break;
    }

    return weight;
  }



  private getDifficultyWeight(
    diffA: string,
    diffB: string,
    skillLevel: 'beginner' | 'intermediate' | 'advanced',
    _prioritizeDifficulty: ('EASY' | 'MEDIUM' | 'HARD')[]
  ): number {
    const difficultyOrder = skillLevel === 'beginner' 
      ? ['EASY', 'MEDIUM', 'HARD']
      : skillLevel === 'intermediate'
      ? ['MEDIUM', 'EASY', 'HARD']
      : ['HARD', 'MEDIUM', 'EASY'];

    const indexA = difficultyOrder.indexOf(diffA as any);
    const indexB = difficultyOrder.indexOf(diffB as any);

    return indexA - indexB;
  }

  // Enhanced problem selection with quality awareness
  private selectQualityAwareProblems(
    sortedProblems: ProblemData[],
    totalNeeded: number,
    targetCompanies: string[],
    skillLevel: 'beginner' | 'intermediate' | 'advanced',
    learningMode: string,
    balanceAcrossCompanies: boolean,
    maxProblemsPerCompany: number,
    adaptiveDifficulty: boolean
  ): StudyProblem[] {
    const selected: StudyProblem[] = [];
    const companyCount: Record<string, number> = {};
    const difficultyCount: Record<string, number> = { EASY: 0, MEDIUM: 0, HARD: 0 };

    // Initialize company counts
    targetCompanies.forEach(company => {
      companyCount[company] = 0;
    });

    // Define target difficulty distribution based on skill level and learning mode
    const targetDistribution = this.getTargetDifficultyDistribution(skillLevel, learningMode);

    for (const problem of sortedProblems) {
      if (selected.length >= totalNeeded) break;

      // Check if we've reached the limit for this company
      if (companyCount[problem.company] >= maxProblemsPerCompany) {
        continue;
      }

      // If balancing, check if this company has too many compared to others
      if (balanceAcrossCompanies) {
        const avgPerCompany = selected.length / targetCompanies.length;
        const currentCompanyCount = companyCount[problem.company];
        
        // Skip if this company already has significantly more than average
        if (currentCompanyCount > avgPerCompany + 2) {
          continue;
        }
      }

      // Check adaptive difficulty distribution
      if (adaptiveDifficulty && selected.length > 10) { // Start checking after first 10 problems
        const currentDistribution = this.getCurrentDifficultyDistribution(selected);
        if (!this.shouldIncludeDifficulty(problem.difficulty, currentDistribution, targetDistribution)) {
          continue;
        }
      }

      // Create enhanced study problem with quality metrics
      const studyProblem: StudyProblem = {
        title: problem.title,
        difficulty: problem.difficulty,
        topics: problem.topics,
        company: problem.company,
        link: problem.link,
        status: 'not_started',
        // Add quality metrics
        qualityScore: this.calculateQualityScore(problem),
        originalityScore: (problem as any).originalityScore,
        likes: (problem as any).likes,
        dislikes: (problem as any).dislikes,
        totalVotes: (problem as any).totalVotes,
        acceptanceRate: problem.acceptanceRate,
        qualityTier: this.getQualityTier(problem),
        recommendationReason: this.getRecommendationReason(problem, learningMode),
        isHiddenGem: this.isHiddenGem(problem),
        isInterviewClassic: this.isInterviewClassic(problem)
      };

      selected.push(studyProblem);
      companyCount[problem.company]++;
      difficultyCount[problem.difficulty as keyof typeof difficultyCount]++;
    }

    return selected;
  }



  // Get target difficulty distribution based on skill level and learning mode
  private getTargetDifficultyDistribution(
    skillLevel: 'beginner' | 'intermediate' | 'advanced',
    learningMode: string
  ): Record<string, number> {
    const baseDistributions = {
      beginner: { EASY: 0.6, MEDIUM: 0.3, HARD: 0.1 },
      intermediate: { EASY: 0.3, MEDIUM: 0.5, HARD: 0.2 },
      advanced: { EASY: 0.1, MEDIUM: 0.4, HARD: 0.5 }
    };

    let distribution = baseDistributions[skillLevel];

    // Adjust based on learning mode
    if (learningMode === 'interview_classics') {
      // Classics tend to be more medium/hard
      distribution = {
        EASY: Math.max(0.1, distribution.EASY - 0.1),
        MEDIUM: distribution.MEDIUM + 0.05,
        HARD: distribution.HARD + 0.05
      };
    } else if (learningMode === 'hidden_gems') {
      // Gems can be more varied, slightly favor medium
      distribution = {
        EASY: distribution.EASY,
        MEDIUM: Math.min(0.6, distribution.MEDIUM + 0.1),
        HARD: Math.max(0.1, distribution.HARD - 0.1)
      };
    }

    return distribution;
  }

  // Get current difficulty distribution
  private getCurrentDifficultyDistribution(problems: StudyProblem[]): Record<string, number> {
    const counts = { EASY: 0, MEDIUM: 0, HARD: 0 };
    problems.forEach(p => {
      if (p.difficulty in counts) {
        counts[p.difficulty as keyof typeof counts]++;
      }
    });

    const total = problems.length;
    return {
      EASY: counts.EASY / total,
      MEDIUM: counts.MEDIUM / total,
      HARD: counts.HARD / total
    };
  }

  // Check if we should include a problem of given difficulty
  private shouldIncludeDifficulty(
    difficulty: string,
    current: Record<string, number>,
    target: Record<string, number>
  ): boolean {
    const currentRatio = current[difficulty] || 0;
    const targetRatio = target[difficulty] || 0;
    
    // Allow if we're under target or within 10% tolerance
    return currentRatio <= targetRatio + 0.1;
  }

  // Get quality tier for a problem
  private getQualityTier(problem: ProblemData): 'Premium' | 'High' | 'Good' | 'Average' | 'Unknown' {
    const qualityScore = this.calculateQualityScore(problem);
    
    if (qualityScore >= 0.8) return 'Premium';
    if (qualityScore >= 0.6) return 'High';
    if (qualityScore >= 0.4) return 'Good';
    if (qualityScore >= 0.2) return 'Average';
    return 'Unknown';
  }

  // Get recommendation reason for a problem
  private getRecommendationReason(problem: ProblemData, learningMode: string): string {
    const isClassic = this.isInterviewClassic(problem);
    const isGem = this.isHiddenGem(problem);
    const qualityScore = this.calculateQualityScore(problem);
    const likes = (problem as any).likes || 0;

    if (isClassic && learningMode === 'interview_classics') {
      return `Interview classic with ${likes.toLocaleString()} likes`;
    }
    
    if (isGem && learningMode === 'hidden_gems') {
      return `Hidden gem with ${(((problem as any).originalityScore || 0.5) * 100).toFixed(0)}% originality`;
    }
    
    if (qualityScore >= 0.8) {
      return `Premium quality problem (${(qualityScore * 100).toFixed(0)}% score)`;
    }
    
    if (qualityScore >= 0.6) {
      return `High quality problem with good community feedback`;
    }
    
    return `Selected for balanced learning approach`;
  }

  // Generate adaptive schedule with progressive difficulty
  private generateAdaptiveSchedule(
    problems: StudyProblem[],
    startDate: string,
    durationWeeks: number,
    dailyGoal: number,
    skillLevel: 'beginner' | 'intermediate' | 'advanced'
  ): StudySession[] {
    const schedule: StudySession[] = [];
    const start = new Date(startDate);
    
    // Sort problems for adaptive progression
    const adaptiveSortedProblems = this.sortProblemsForAdaptiveProgression(problems, skillLevel);
    
    let problemIndex = 0;

    for (let week = 0; week < durationWeeks; week++) {
      // Get weekly difficulty preferences
      const weeklyPreferences = this.getWeeklyDifficultyPreferences(week + 1, skillLevel);
      
      for (let day = 0; day < 7; day++) {
        const currentDate = new Date(start);
        currentDate.setDate(start.getDate() + (week * 7) + day);

        const dailyProblems: StudyProblem[] = [];
        
        // Select problems for this day based on weekly preferences
        const dayProblems = this.selectDailyProblemsAdaptive(
          adaptiveSortedProblems.slice(problemIndex),
          dailyGoal,
          weeklyPreferences,
          week + 1
        );
        
        dayProblems.forEach(problem => {
          dailyProblems.push({ ...problem });
          problemIndex++;
        });

        if (dailyProblems.length > 0) {
          schedule.push({
            id: this.generateId(),
            date: currentDate.toISOString().split('T')[0],
            problems: dailyProblems,
            completed: false
          });
        }
      }
    }

    return schedule;
  }

  // Generate daily schedule (legacy method)
  private generateSchedule(
    problems: StudyProblem[],
    startDate: string,
    durationWeeks: number,
    dailyGoal: number
  ): StudySession[] {
    const schedule: StudySession[] = [];
    const start = new Date(startDate);
    let problemIndex = 0;

    for (let week = 0; week < durationWeeks; week++) {
      for (let day = 0; day < 7; day++) {
        const currentDate = new Date(start);
        currentDate.setDate(start.getDate() + (week * 7) + day);

        const dailyProblems: StudyProblem[] = [];
        
        // Add problems for this day
        for (let i = 0; i < dailyGoal && problemIndex < problems.length; i++) {
          dailyProblems.push({ ...problems[problemIndex] });
          problemIndex++;
        }

        if (dailyProblems.length > 0) {
          schedule.push({
            id: this.generateId(),
            date: currentDate.toISOString().split('T')[0], // YYYY-MM-DD format
            problems: dailyProblems,
            completed: false
          });
        }
      }
    }

    return schedule;
  }

  // Sort problems for adaptive progression
  private sortProblemsForAdaptiveProgression(
    problems: StudyProblem[],
    skillLevel: 'beginner' | 'intermediate' | 'advanced'
  ): StudyProblem[] {
    // Create difficulty order based on skill level
    const difficultyOrder = skillLevel === 'beginner' 
      ? ['EASY', 'MEDIUM', 'HARD']
      : skillLevel === 'intermediate'
      ? ['EASY', 'MEDIUM', 'HARD'] // Mixed approach
      : ['MEDIUM', 'EASY', 'HARD']; // Advanced starts with medium

    return problems.sort((a, b) => {
      // First sort by quality (higher quality first within each difficulty)
      const qualityDiff = (b.qualityScore || 0) - (a.qualityScore || 0);
      if (Math.abs(qualityDiff) > 0.1) return qualityDiff;

      // Then by difficulty progression
      const aDiffIndex = difficultyOrder.indexOf(a.difficulty);
      const bDiffIndex = difficultyOrder.indexOf(b.difficulty);
      if (aDiffIndex !== bDiffIndex) {
        return aDiffIndex - bDiffIndex;
      }

      // Finally by acceptance rate (easier first for same difficulty)
      const aAcceptance = a.acceptanceRate || 0.5;
      const bAcceptance = b.acceptanceRate || 0.5;
      return bAcceptance - aAcceptance;
    });
  }

  // Get weekly difficulty preferences for adaptive progression
  private getWeeklyDifficultyPreferences(
    week: number,
    skillLevel: 'beginner' | 'intermediate' | 'advanced'
  ): Record<string, number> {
    const progressions = {
      beginner: {
        1: { EASY: 0.8, MEDIUM: 0.2, HARD: 0.0 },
        2: { EASY: 0.7, MEDIUM: 0.3, HARD: 0.0 },
        3: { EASY: 0.6, MEDIUM: 0.4, HARD: 0.0 },
        4: { EASY: 0.5, MEDIUM: 0.4, HARD: 0.1 },
        5: { EASY: 0.4, MEDIUM: 0.5, HARD: 0.1 },
        6: { EASY: 0.3, MEDIUM: 0.6, HARD: 0.1 },
        7: { EASY: 0.3, MEDIUM: 0.6, HARD: 0.1 },
        8: { EASY: 0.2, MEDIUM: 0.6, HARD: 0.2 }
      },
      intermediate: {
        1: { EASY: 0.5, MEDIUM: 0.5, HARD: 0.0 },
        2: { EASY: 0.4, MEDIUM: 0.6, HARD: 0.0 },
        3: { EASY: 0.3, MEDIUM: 0.6, HARD: 0.1 },
        4: { EASY: 0.3, MEDIUM: 0.5, HARD: 0.2 },
        5: { EASY: 0.2, MEDIUM: 0.6, HARD: 0.2 },
        6: { EASY: 0.2, MEDIUM: 0.5, HARD: 0.3 },
        7: { EASY: 0.1, MEDIUM: 0.6, HARD: 0.3 },
        8: { EASY: 0.1, MEDIUM: 0.5, HARD: 0.4 }
      },
      advanced: {
        1: { EASY: 0.3, MEDIUM: 0.6, HARD: 0.1 },
        2: { EASY: 0.2, MEDIUM: 0.6, HARD: 0.2 },
        3: { EASY: 0.2, MEDIUM: 0.5, HARD: 0.3 },
        4: { EASY: 0.1, MEDIUM: 0.6, HARD: 0.3 },
        5: { EASY: 0.1, MEDIUM: 0.5, HARD: 0.4 },
        6: { EASY: 0.1, MEDIUM: 0.4, HARD: 0.5 },
        7: { EASY: 0.0, MEDIUM: 0.4, HARD: 0.6 },
        8: { EASY: 0.0, MEDIUM: 0.3, HARD: 0.7 }
      }
    };

    const skillProgression = progressions[skillLevel];
    const weekKey = Math.min(week, 8);
    return skillProgression[weekKey as keyof typeof skillProgression] || skillProgression[8];
  }

  // Select daily problems based on adaptive preferences
  private selectDailyProblemsAdaptive(
    availableProblems: StudyProblem[],
    dailyGoal: number,
    weeklyPreferences: Record<string, number>,
    _week: number
  ): StudyProblem[] {
    const selected: StudyProblem[] = [];
    const targetCounts = {
      EASY: Math.round(dailyGoal * weeklyPreferences.EASY),
      MEDIUM: Math.round(dailyGoal * weeklyPreferences.MEDIUM),
      HARD: Math.round(dailyGoal * weeklyPreferences.HARD)
    };

    // Adjust if rounding doesn't add up to dailyGoal
    const totalTargeted = targetCounts.EASY + targetCounts.MEDIUM + targetCounts.HARD;
    if (totalTargeted < dailyGoal) {
      // Add to the most preferred difficulty
      const maxDifficulty = Object.entries(weeklyPreferences)
        .reduce((a, b) => weeklyPreferences[a[0]] > weeklyPreferences[b[0]] ? a : b)[0];
      targetCounts[maxDifficulty as keyof typeof targetCounts]++;
    }

    // Select problems by difficulty
    const counts = { EASY: 0, MEDIUM: 0, HARD: 0 };
    
    for (const problem of availableProblems) {
      if (selected.length >= dailyGoal) break;
      
      const difficulty = problem.difficulty as keyof typeof counts;
      if (counts[difficulty] < targetCounts[difficulty]) {
        selected.push(problem);
        counts[difficulty]++;
      }
    }

    // Fill remaining slots with any available problems
    for (const problem of availableProblems) {
      if (selected.length >= dailyGoal) break;
      if (!selected.includes(problem)) {
        selected.push(problem);
      }
    }

    return selected.slice(0, dailyGoal);
  }

  // Initialize progress tracking
  private initializeProgress(problems: StudyProblem[]): StudyProgress {
    const difficultyBreakdown = {
      EASY: { completed: 0, total: 0 },
      MEDIUM: { completed: 0, total: 0 },
      HARD: { completed: 0, total: 0 }
    };

    const topicProgress: Record<string, { completed: number; total: number }> = {};
    const companyProgress: Record<string, { completed: number; total: number }> = {};

    problems.forEach(problem => {
      // Count by difficulty
      if (problem.difficulty in difficultyBreakdown) {
        difficultyBreakdown[problem.difficulty as keyof typeof difficultyBreakdown].total++;
      }

      // Count by topics
      problem.topics.forEach(topic => {
        if (!topicProgress[topic]) {
          topicProgress[topic] = { completed: 0, total: 0 };
        }
        topicProgress[topic].total++;
      });

      // Count by company
      if (!companyProgress[problem.company]) {
        companyProgress[problem.company] = { completed: 0, total: 0 };
      }
      companyProgress[problem.company].total++;
    });

    return {
      totalProblems: problems.length,
      completedProblems: 0,
      skippedProblems: 0,
      currentStreak: 0,
      longestStreak: 0,
      averageProblemsPerDay: 0,
      completionRate: 0,
      difficultyBreakdown,
      topicProgress,
      companyProgress
    };
  }

  // Save study plan to localStorage with backup
  saveStudyPlan(studyPlan: StudyPlan): void {
    const existingPlans = this.getStudyPlans();
    const updatedPlans = existingPlans.filter(plan => plan.id !== studyPlan.id);
    updatedPlans.push({
      ...studyPlan,
      updatedAt: new Date().toISOString()
    });
    
    try {
      // Save to primary storage
      localStorage.setItem(this.STORAGE_KEY, JSON.stringify(updatedPlans));
      
      // Create backup every time we save
      this.createBackup(updatedPlans);
      
      // Check if we should remind user to export
      this.checkExportReminder();
      
    } catch (error) {
      console.error('Failed to save study plan:', error);
      // Try to save to backup location
      try {
        localStorage.setItem(this.BACKUP_KEY, JSON.stringify(updatedPlans));
      } catch (backupError) {
        console.error('Failed to save backup:', backupError);
        throw new Error('Storage quota exceeded. Please export your data and clear some space.');
      }
    }
  }

  // Get all study plans from localStorage
  getStudyPlans(): StudyPlan[] {
    try {
      const stored = localStorage.getItem(this.STORAGE_KEY);
      return stored ? JSON.parse(stored) : [];
    } catch (error) {
      console.error('Error loading study plans:', error);
      return [];
    }
  }

  // Get a specific study plan by ID
  getStudyPlan(id: string): StudyPlan | null {
    const plans = this.getStudyPlans();
    return plans.find(plan => plan.id === id) || null;
  }

  // Delete a study plan
  deleteStudyPlan(id: string): void {
    const plans = this.getStudyPlans();
    const updatedPlans = plans.filter(plan => plan.id !== id);
    localStorage.setItem(this.STORAGE_KEY, JSON.stringify(updatedPlans));
  }

  // Update problem status and recalculate progress
  updateProblemStatus(
    studyPlanId: string,
    sessionId: string,
    problemTitle: string,
    status: StudyProblem['status'],
    notes?: string
  ): void {
    const studyPlan = this.getStudyPlan(studyPlanId);
    if (!studyPlan) return;

    // Find and update the problem
    const session = studyPlan.schedule.find(s => s.id === sessionId);
    if (!session) return;

    const problem = session.problems.find(p => p.title === problemTitle);
    if (!problem) return;

    problem.status = status;
    problem.notes = notes;

    if (status === 'completed') {
      problem.completedAt = new Date().toISOString();
    }

    // Check if session is completed
    session.completed = session.problems.every(p => 
      p.status === 'completed' || p.status === 'skipped'
    );

    if (session.completed && !session.completedAt) {
      session.completedAt = new Date().toISOString();
    }

    // Recalculate progress
    studyPlan.progress = this.calculateProgress(studyPlan);

    // Save updated plan
    this.saveStudyPlan(studyPlan);
  }

  // Calculate current progress
  private calculateProgress(studyPlan: StudyPlan): StudyProgress {
    const allProblems = studyPlan.schedule.flatMap(session => session.problems);
    
    const completedProblems = allProblems.filter(p => p.status === 'completed').length;
    const skippedProblems = allProblems.filter(p => p.status === 'skipped').length;
    
    // Calculate difficulty breakdown
    const difficultyBreakdown = {
      EASY: { completed: 0, total: 0 },
      MEDIUM: { completed: 0, total: 0 },
      HARD: { completed: 0, total: 0 }
    };

    const topicProgress: Record<string, { completed: number; total: number }> = {};
    const companyProgress: Record<string, { completed: number; total: number }> = {};

    allProblems.forEach(problem => {
      // Count by difficulty
      if (problem.difficulty in difficultyBreakdown) {
        const diffKey = problem.difficulty as keyof typeof difficultyBreakdown;
        difficultyBreakdown[diffKey].total++;
        if (problem.status === 'completed') {
          difficultyBreakdown[diffKey].completed++;
        }
      }

      // Count by topics
      problem.topics.forEach(topic => {
        if (!topicProgress[topic]) {
          topicProgress[topic] = { completed: 0, total: 0 };
        }
        topicProgress[topic].total++;
        if (problem.status === 'completed') {
          topicProgress[topic].completed++;
        }
      });

      // Count by company
      if (!companyProgress[problem.company]) {
        companyProgress[problem.company] = { completed: 0, total: 0 };
      }
      companyProgress[problem.company].total++;
      if (problem.status === 'completed') {
        companyProgress[problem.company].completed++;
      }
    });

    // Calculate streaks
    const { currentStreak, longestStreak } = this.calculateStreaks(studyPlan.schedule);

    // Calculate average problems per day
    const completedSessions = studyPlan.schedule.filter(s => s.completed);
    const averageProblemsPerDay = completedSessions.length > 0 
      ? completedProblems / completedSessions.length 
      : 0;

    return {
      totalProblems: allProblems.length,
      completedProblems,
      skippedProblems,
      currentStreak,
      longestStreak,
      averageProblemsPerDay,
      completionRate: allProblems.length > 0 ? (completedProblems / allProblems.length) * 100 : 0,
      difficultyBreakdown,
      topicProgress,
      companyProgress
    };
  }

  // Calculate study streaks
  private calculateStreaks(schedule: StudySession[]): { currentStreak: number; longestStreak: number } {
    const sortedSessions = schedule
      .filter(s => s.completed)
      .sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());

    let currentStreak = 0;
    let longestStreak = 0;
    let tempStreak = 0;

    const today = new Date();
    today.setHours(0, 0, 0, 0);

    for (let i = 0; i < sortedSessions.length; i++) {
      const sessionDate = new Date(sortedSessions[i].date);
      sessionDate.setHours(0, 0, 0, 0);

      if (i === 0) {
        tempStreak = 1;
      } else {
        const prevDate = new Date(sortedSessions[i - 1].date);
        prevDate.setHours(0, 0, 0, 0);
        
        const daysDiff = (sessionDate.getTime() - prevDate.getTime()) / (1000 * 60 * 60 * 24);
        
        if (daysDiff === 1) {
          tempStreak++;
        } else {
          tempStreak = 1;
        }
      }

      longestStreak = Math.max(longestStreak, tempStreak);

      // Check if this contributes to current streak
      const daysSinceSession = (today.getTime() - sessionDate.getTime()) / (1000 * 60 * 60 * 24);
      if (daysSinceSession <= 1) {
        currentStreak = tempStreak;
      }
    }

    return { currentStreak, longestStreak };
  }

  // Create backup of study plans
  private createBackup(plans: StudyPlan[]): void {
    try {
      const backup = {
        timestamp: new Date().toISOString(),
        plans: plans,
        version: '1.0'
      };
      localStorage.setItem(this.BACKUP_KEY, JSON.stringify(backup));
    } catch (error) {
      console.warn('Failed to create backup:', error);
    }
  }

  // Check if user should be reminded to export data
  private checkExportReminder(): void {
    const lastReminder = localStorage.getItem(this.EXPORT_KEY);
    const now = new Date().getTime();
    const reminderInterval = 7 * 24 * 60 * 60 * 1000; // 7 days
    
    if (!lastReminder || (now - parseInt(lastReminder)) > reminderInterval) {
      // Set reminder for next time
      localStorage.setItem(this.EXPORT_KEY, now.toString());
      
      // Show reminder (could be enhanced with a proper notification system)
      console.info('💡 Tip: Consider exporting your study plans to avoid data loss!');
    }
  }

  // Export study plans to JSON file
  exportStudyPlans(): string {
    const plans = this.getStudyPlans();
    const exportData = {
      exportDate: new Date().toISOString(),
      version: '1.0',
      studyPlans: plans
    };
    
    return JSON.stringify(exportData, null, 2);
  }

  // Import study plans from JSON
  importStudyPlans(jsonData: string): { success: boolean; message: string; imported: number } {
    try {
      const importData = JSON.parse(jsonData);
      
      if (!importData.studyPlans || !Array.isArray(importData.studyPlans)) {
        return { success: false, message: 'Invalid file format', imported: 0 };
      }
      
      const existingPlans = this.getStudyPlans();
      const existingIds = new Set(existingPlans.map(p => p.id));
      
      let importedCount = 0;
      const newPlans = [...existingPlans];
      
      for (const plan of importData.studyPlans) {
        // Validate plan structure
        if (this.isValidStudyPlan(plan)) {
          if (!existingIds.has(plan.id)) {
            newPlans.push(plan);
            importedCount++;
          }
        }
      }
      
      if (importedCount > 0) {
        localStorage.setItem(this.STORAGE_KEY, JSON.stringify(newPlans));
        this.createBackup(newPlans);
      }
      
      return { 
        success: true, 
        message: `Successfully imported ${importedCount} study plans`, 
        imported: importedCount 
      };
      
    } catch (error) {
      return { success: false, message: 'Failed to parse file', imported: 0 };
    }
  }

  // Validate study plan structure
  private isValidStudyPlan(plan: any): boolean {
    return plan && 
           typeof plan.id === 'string' &&
           typeof plan.name === 'string' &&
           Array.isArray(plan.targetCompanies) &&
           typeof plan.duration === 'number' &&
           typeof plan.dailyGoal === 'number' &&
           Array.isArray(plan.schedule) &&
           plan.progress;
  }

  // Restore from backup if main storage is corrupted
  restoreFromBackup(): boolean {
    try {
      const backupData = localStorage.getItem(this.BACKUP_KEY);
      if (!backupData) return false;
      
      const backup = JSON.parse(backupData);
      if (backup.plans && Array.isArray(backup.plans)) {
        localStorage.setItem(this.STORAGE_KEY, JSON.stringify(backup.plans));
        return true;
      }
      return false;
    } catch (error) {
      console.error('Failed to restore from backup:', error);
      return false;
    }
  }

  // Get storage usage information
  getStorageInfo(): { used: number; available: number; percentage: number } {
    try {
      const plans = JSON.stringify(this.getStudyPlans());
      const used = new Blob([plans]).size;
      
      // Estimate available space (localStorage is typically 5-10MB)
      const estimated = 5 * 1024 * 1024; // 5MB conservative estimate
      const percentage = (used / estimated) * 100;
      
      return {
        used: Math.round(used / 1024), // KB
        available: Math.round((estimated - used) / 1024), // KB
        percentage: Math.round(percentage)
      };
    } catch (error) {
      return { used: 0, available: 0, percentage: 0 };
    }
  }

  // Clear all data (with confirmation)
  clearAllData(): void {
    localStorage.removeItem(this.STORAGE_KEY);
    localStorage.removeItem(this.BACKUP_KEY);
    localStorage.removeItem(this.EXPORT_KEY);
  }

  // Generate unique ID
  private generateId(): string {
    return Date.now().toString(36) + Math.random().toString(36).substr(2);
  }

  // Get recommended focus areas based on common topics
  getRecommendedFocusAreas(): string[] {
    return [
      'Arrays',
      'Dynamic Programming',
      'Trees',
      'Graphs',
      'Hash Tables',
      'Strings',
      'Linked Lists',
      'Binary Search',
      'Sorting',
      'Two Pointers',
      'Sliding Window',
      'Backtracking',
      'Greedy',
      'Stack',
      'Queue',
      'Heap',
      'Trie',
      'Union Find',
      'Bit Manipulation',
      'Math'
    ];
  }

  // Generate personalized feedback and recommendations based on performance
  generateFeedback(studyPlan: StudyPlan): {
    feedback: string[];
    recommendations: string[];
    insights: string[];
  } {
    const progress = studyPlan.progress;
    const feedback: string[] = [];
    const recommendations: string[] = [];
    const insights: string[] = [];

    // Completion rate feedback
    if (progress.completionRate >= 80) {
      feedback.push("🎉 Excellent progress! You're doing great with your study plan.");
    } else if (progress.completionRate >= 60) {
      feedback.push("👍 Good progress! Keep up the momentum.");
    } else if (progress.completionRate >= 40) {
      feedback.push("📈 You're making steady progress. Consider increasing your daily focus time.");
    } else {
      feedback.push("💪 Every expert was once a beginner. Stay consistent and you'll see improvement!");
    }

    // Streak feedback
    if (progress.currentStreak >= 7) {
      feedback.push(`🔥 Amazing ${progress.currentStreak}-day streak! Consistency is key to success.`);
    } else if (progress.currentStreak >= 3) {
      feedback.push(`⭐ Great ${progress.currentStreak}-day streak! Try to extend it further.`);
    } else if (progress.currentStreak === 0 && progress.longestStreak > 0) {
      feedback.push(`🎯 Your best streak was ${progress.longestStreak} days. You can achieve it again!`);
    }

    // Difficulty analysis and recommendations
    const { EASY, MEDIUM, HARD } = progress.difficultyBreakdown;
    const easyRate = EASY.total > 0 ? EASY.completed / EASY.total : 0;
    const mediumRate = MEDIUM.total > 0 ? MEDIUM.completed / MEDIUM.total : 0;
    const hardRate = HARD.total > 0 ? HARD.completed / HARD.total : 0;

    if (easyRate < 0.8 && EASY.total > 0) {
      recommendations.push("Focus on completing more EASY problems to build confidence and fundamentals.");
    }
    
    if (easyRate >= 0.8 && mediumRate < 0.6 && MEDIUM.total > 0) {
      recommendations.push("Great job with easy problems! Now challenge yourself with more MEDIUM difficulty problems.");
    }
    
    if (mediumRate >= 0.7 && hardRate < 0.4 && HARD.total > 0) {
      recommendations.push("You're ready for HARD problems! They'll prepare you for senior-level interviews.");
    }

    // Topic-based insights
    const topicEntries = Object.entries(progress.topicProgress);
    const strugglingTopics = topicEntries
      .filter(([_, stats]) => stats.total >= 3 && (stats.completed / stats.total) < 0.5)
      .map(([topic]) => topic);
    
    const strongTopics = topicEntries
      .filter(([_, stats]) => stats.total >= 3 && (stats.completed / stats.total) >= 0.8)
      .map(([topic]) => topic);

    if (strugglingTopics.length > 0) {
      insights.push(`📚 Topics needing attention: ${strugglingTopics.slice(0, 3).join(', ')}`);
      recommendations.push(`Consider reviewing fundamentals for: ${strugglingTopics.slice(0, 2).join(', ')}`);
    }

    if (strongTopics.length > 0) {
      insights.push(`💪 Your strong areas: ${strongTopics.slice(0, 3).join(', ')}`);
    }

    // Velocity-based recommendations
    if (progress.averageProblemsPerDay < studyPlan.dailyGoal * 0.7) {
      recommendations.push("Try breaking study sessions into smaller chunks throughout the day.");
      recommendations.push("Consider reducing daily goal temporarily to build consistency.");
    } else if (progress.averageProblemsPerDay > studyPlan.dailyGoal * 1.2) {
      recommendations.push("Excellent pace! Consider increasing your daily goal or adding harder problems.");
    }

    // Company-specific insights
    const companyEntries = Object.entries(progress.companyProgress);
    const laggingCompanies = companyEntries
      .filter(([_, stats]) => stats.total >= 5 && (stats.completed / stats.total) < 0.5)
      .map(([company]) => company);

    if (laggingCompanies.length > 0) {
      insights.push(`🎯 Focus more on ${laggingCompanies[0]} problems to match your target companies.`);
    }

    // Skipped problems analysis
    if (progress.skippedProblems > progress.completedProblems * 0.3) {
      recommendations.push("You're skipping many problems. Try spending more time understanding before skipping.");
      recommendations.push("Consider reviewing skipped problems - they might be easier on second attempt.");
    }

    return { feedback, recommendations, insights };
  }

  // Get adaptive recommendations for next problems based on performance
  getAdaptiveRecommendations(studyPlan: StudyPlan): {
    suggestedDifficulty: ('EASY' | 'MEDIUM' | 'HARD')[];
    suggestedTopics: string[];
    suggestedCompanies: string[];
    reasoning: string;
  } {
    const progress = studyPlan.progress;
    const { EASY, MEDIUM, HARD } = progress.difficultyBreakdown;
    
    // Calculate success rates
    const easyRate = EASY.total > 0 ? EASY.completed / EASY.total : 0;
    const mediumRate = MEDIUM.total > 0 ? MEDIUM.completed / MEDIUM.total : 0;
    const hardRate = HARD.total > 0 ? HARD.completed / HARD.total : 0;

    let suggestedDifficulty: ('EASY' | 'MEDIUM' | 'HARD')[] = [];
    let reasoning = '';

    // Adaptive difficulty recommendation
    if (easyRate < 0.7) {
      suggestedDifficulty = ['EASY', 'MEDIUM'];
      reasoning = 'Focus on easy problems to build fundamentals before advancing.';
    } else if (mediumRate < 0.6) {
      suggestedDifficulty = ['MEDIUM', 'EASY'];
      reasoning = 'Good foundation! Time to challenge yourself with medium problems.';
    } else if (hardRate < 0.4) {
      suggestedDifficulty = ['HARD', 'MEDIUM'];
      reasoning = 'Ready for hard problems! These will prepare you for senior interviews.';
    } else {
      suggestedDifficulty = ['HARD', 'MEDIUM', 'EASY'];
      reasoning = 'Excellent performance! Continue with challenging problems.';
    }

    // Topic recommendations based on weak areas
    const topicEntries = Object.entries(progress.topicProgress);
    const weakTopics = topicEntries
      .filter(([_, stats]) => stats.total >= 2 && (stats.completed / stats.total) < 0.6)
      .sort((a, b) => (a[1].completed / a[1].total) - (b[1].completed / b[1].total))
      .map(([topic]) => topic)
      .slice(0, 3);

    const suggestedTopics = weakTopics.length > 0 ? weakTopics : [
      'Arrays', 'Dynamic Programming', 'Trees' // Default high-frequency topics
    ];

    // Company recommendations based on target companies and performance
    const companyEntries = Object.entries(progress.companyProgress);
    const laggingCompanies = companyEntries
      .filter(([company, stats]) => 
        studyPlan.targetCompanies.includes(company) && 
        stats.total >= 3 && 
        (stats.completed / stats.total) < 0.6
      )
      .sort((a, b) => (a[1].completed / a[1].total) - (b[1].completed / b[1].total))
      .map(([company]) => company);

    const suggestedCompanies = laggingCompanies.length > 0 
      ? laggingCompanies.slice(0, 2)
      : studyPlan.targetCompanies.slice(0, 2);

    return {
      suggestedDifficulty,
      suggestedTopics,
      suggestedCompanies,
      reasoning
    };
  }

  // Get quality-based insights for a study plan
  getQualityInsights(studyPlan: StudyPlan): {
    qualityDistribution: Record<string, number>;
    averageQualityScore: number;
    hiddenGemsCount: number;
    interviewClassicsCount: number;
    qualityRecommendations: string[];
    learningModeEffectiveness: string;
  } {
    const allProblems = studyPlan.schedule.flatMap(session => session.problems);
    const problemsWithQuality = allProblems.filter(p => p.qualityScore !== undefined);
    
    if (problemsWithQuality.length === 0) {
      return {
        qualityDistribution: {},
        averageQualityScore: 0,
        hiddenGemsCount: 0,
        interviewClassicsCount: 0,
        qualityRecommendations: ['Quality metrics not available for this study plan'],
        learningModeEffectiveness: 'Unable to assess without quality data'
      };
    }

    // Calculate quality distribution
    const qualityDistribution: Record<string, number> = {
      'Premium': 0,
      'High': 0,
      'Good': 0,
      'Average': 0,
      'Unknown': 0
    };

    let totalQualityScore = 0;
    let hiddenGemsCount = 0;
    let interviewClassicsCount = 0;

    problemsWithQuality.forEach(problem => {
      if (problem.qualityTier) {
        qualityDistribution[problem.qualityTier]++;
      }
      if (problem.qualityScore) {
        totalQualityScore += problem.qualityScore;
      }
      if (problem.isHiddenGem) {
        hiddenGemsCount++;
      }
      if (problem.isInterviewClassic) {
        interviewClassicsCount++;
      }
    });

    const averageQualityScore = totalQualityScore / problemsWithQuality.length;

    // Generate quality recommendations
    const qualityRecommendations: string[] = [];
    
    // Calculate ratios for recommendations
    const hiddenGemsRatio = hiddenGemsCount / problemsWithQuality.length;
    const classicsRatio = interviewClassicsCount / problemsWithQuality.length;

    if (averageQualityScore >= 0.8) {
      qualityRecommendations.push('Excellent quality selection! Your study plan focuses on high-originality problems.');
    } else if (averageQualityScore >= 0.6) {
      qualityRecommendations.push('Good quality balance. Consider adding more premium problems for deeper learning.');
    } else {
      qualityRecommendations.push('Consider focusing on higher quality problems to maximize learning efficiency.');
    }

    if (hiddenGemsRatio >= 0.3) {
      qualityRecommendations.push('Great discovery focus! Hidden gems will expose you to unique problem-solving approaches.');
    } else if (hiddenGemsRatio < 0.1) {
      qualityRecommendations.push('Consider adding hidden gems to discover innovative problem-solving techniques.');
    }

    if (classicsRatio >= 0.4) {
      qualityRecommendations.push('Strong foundation with interview classics. You\'re covering essential patterns.');
    } else if (classicsRatio < 0.2) {
      qualityRecommendations.push('Add more interview classics to ensure you cover fundamental patterns.');
    }

    // Assess learning mode effectiveness
    let learningModeEffectiveness = '';
    if (hiddenGemsRatio > classicsRatio) {
      learningModeEffectiveness = 'Discovery-focused approach - excellent for learning unique techniques';
    } else if (classicsRatio > hiddenGemsRatio * 2) {
      learningModeEffectiveness = 'Foundation-focused approach - great for mastering core patterns';
    } else {
      learningModeEffectiveness = 'Balanced approach - good mix of fundamentals and innovation';
    }

    return {
      qualityDistribution,
      averageQualityScore,
      hiddenGemsCount,
      interviewClassicsCount,
      qualityRecommendations,
      learningModeEffectiveness
    };
  }

  // Get next recommended problems based on quality and performance
  getQualityBasedNextProblems(
    studyPlan: StudyPlan,
    availableProblems: ProblemData[],
    count: number = 5
  ): StudyProblem[] {
    const adaptiveRecs = this.getAdaptiveRecommendations(studyPlan);
    const qualityInsights = this.getQualityInsights(studyPlan);
    
    // Filter available problems based on adaptive recommendations
    const filteredProblems = availableProblems.filter(problem => {
      // Check if difficulty matches recommendations
      const difficultyMatch = adaptiveRecs.suggestedDifficulty.includes(problem.difficulty as any);
      
      // Check if topics match recommendations
      const topicMatch = adaptiveRecs.suggestedTopics.length === 0 || 
        problem.topics.some(topic => 
          adaptiveRecs.suggestedTopics.some(suggestedTopic => 
            topic.toLowerCase().includes(suggestedTopic.toLowerCase())
          )
        );
      
      // Check if company matches recommendations
      const companyMatch = adaptiveRecs.suggestedCompanies.length === 0 ||
        adaptiveRecs.suggestedCompanies.includes(problem.company);
      
      return difficultyMatch && (topicMatch || companyMatch);
    });

    // Apply quality-based prioritization
    const prioritizedProblems = this.prioritizeProblemsWithQuality(
      filteredProblems,
      'intermediate', // Default to intermediate for recommendations
      adaptiveRecs.suggestedDifficulty,
      qualityInsights.hiddenGemsCount < qualityInsights.interviewClassicsCount ? 'hidden_gems' : 'interview_classics',
      'quality_first'
    );

    // Convert to StudyProblems with quality metrics
    return prioritizedProblems.slice(0, count).map(problem => ({
      title: problem.title,
      difficulty: problem.difficulty,
      topics: problem.topics,
      company: problem.company,
      link: problem.link,
      status: 'not_started' as const,
      qualityScore: this.calculateQualityScore(problem),
      originalityScore: (problem as any).originalityScore,
      likes: (problem as any).likes,
      dislikes: (problem as any).dislikes,
      totalVotes: (problem as any).totalVotes,
      acceptanceRate: problem.acceptanceRate,
      qualityTier: this.getQualityTier(problem),
      recommendationReason: `Recommended based on your progress in ${adaptiveRecs.reasoning}`,
      isHiddenGem: this.isHiddenGem(problem),
      isInterviewClassic: this.isInterviewClassic(problem)
    }));
  }
}

export const studyPlanService = new StudyPlanService();
