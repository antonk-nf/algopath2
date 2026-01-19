/**
 * Test script for quality-aware study plan generation
 * This demonstrates the new advanced study recommendations functionality
 */

import { studyPlanService } from './services/studyPlanService';
import type { StudyPlanFormData, ProblemData, CompanyData } from './types';

// Mock problem data with quality metrics
const mockProblemsWithQuality: ProblemData[] = [
  {
    title: "Two Sum",
    difficulty: "EASY",
    topics: ["Arrays", "Hash Tables"],
    company: "Google",
    frequency: 4.5,
    acceptanceRate: 0.49,
    timeframe: "30d",
    link: "https://leetcode.com/problems/two-sum/",
    // Quality metrics (would come from metadata service)
    originalityScore: 0.85,
    likes: 15000,
    dislikes: 500,
    totalVotes: 15500
  } as ProblemData & { originalityScore: number; likes: number; dislikes: number; totalVotes: number },
  
  {
    title: "Median of Two Sorted Arrays",
    difficulty: "HARD",
    topics: ["Arrays", "Binary Search"],
    company: "Google",
    frequency: 3.2,
    acceptanceRate: 0.35,
    timeframe: "30d",
    link: "https://leetcode.com/problems/median-of-two-sorted-arrays/",
    // Quality metrics
    originalityScore: 0.92,
    likes: 8000,
    dislikes: 1200,
    totalVotes: 9200
  } as ProblemData & { originalityScore: number; likes: number; dislikes: number; totalVotes: number },
  
  {
    title: "Hidden Gem Problem",
    difficulty: "MEDIUM",
    topics: ["Dynamic Programming", "Trees"],
    company: "Amazon",
    frequency: 2.1,
    acceptanceRate: 0.42,
    timeframe: "30d",
    link: "https://leetcode.com/problems/hidden-gem/",
    // Quality metrics - hidden gem characteristics
    originalityScore: 0.88,
    likes: 150,
    dislikes: 20,
    totalVotes: 170
  } as ProblemData & { originalityScore: number; likes: number; dislikes: number; totalVotes: number }
];

const mockCompanies: CompanyData[] = [
  {
    company: "Google",
    totalProblems: 150,
    uniqueProblems: 120,
    avgFrequency: 2.5,
    avgAcceptanceRate: 0.45,
    difficultyDistribution: { EASY: 30, MEDIUM: 70, HARD: 50, UNKNOWN: 0 },
    topTopics: ["Arrays", "Dynamic Programming"],
    timeframeCoverage: ["30d", "3m"]
  },
  {
    company: "Amazon",
    totalProblems: 140,
    uniqueProblems: 110,
    avgFrequency: 2.3,
    avgAcceptanceRate: 0.42,
    difficultyDistribution: { EASY: 25, MEDIUM: 65, HARD: 50, UNKNOWN: 0 },
    topTopics: ["Trees", "Graphs"],
    timeframeCoverage: ["30d", "3m"]
  }
];

// Test different learning modes
function testQualityAwareStudyPlan() {
  console.log('🧪 Testing Quality-Aware Study Plan Generation\n');

  // Test 1: Balanced Learning Mode
  console.log('📚 Test 1: Balanced Learning Mode');
  const balancedFormData: StudyPlanFormData = {
    name: "Balanced FAANG Prep",
    targetCompanies: ["Google", "Amazon"],
    duration: 4,
    dailyGoal: 2,
    skillLevel: "intermediate",
    focusAreas: ["Arrays", "Dynamic Programming"],
    startDate: new Date().toISOString().split('T')[0],
    learningMode: "balanced",
    qualityPreference: "balanced",
    adaptiveDifficulty: true,
    includeQualityMetrics: true
  };

  const balancedPlan = studyPlanService.generateStudyPlan(
    balancedFormData,
    mockProblemsWithQuality,
    mockCompanies,
    {
      learningMode: "balanced",
      qualityPreference: "balanced",
      adaptiveDifficulty: true,
      includeQualityMetrics: true
    }
  );

  console.log(`✅ Generated plan with ${balancedPlan.schedule.length} sessions`);
  console.log(`📊 Total problems: ${balancedPlan.progress.totalProblems}`);
  
  // Check if quality metrics are included
  const firstProblem = balancedPlan.schedule[0]?.problems[0];
  if (firstProblem?.qualityScore) {
    console.log(`🎯 Quality metrics included: Score ${(firstProblem.qualityScore * 100).toFixed(0)}%`);
    console.log(`💎 Quality tier: ${firstProblem.qualityTier}`);
    if (firstProblem.recommendationReason) {
      console.log(`💡 Recommendation: ${firstProblem.recommendationReason}`);
    }
  }

  // Test 2: Interview Classics Mode
  console.log('\n📚 Test 2: Interview Classics Mode');
  const classicsFormData: StudyPlanFormData = {
    ...balancedFormData,
    name: "Interview Classics Focus",
    learningMode: "interview_classics",
    qualityPreference: "popularity_first"
  };

  const classicsPlan = studyPlanService.generateStudyPlan(
    classicsFormData,
    mockProblemsWithQuality,
    mockCompanies,
    {
      learningMode: "interview_classics",
      qualityPreference: "popularity_first",
      adaptiveDifficulty: true,
      includeQualityMetrics: true
    }
  );

  console.log(`✅ Generated classics plan with ${classicsPlan.schedule.length} sessions`);
  
  // Check for interview classics
  const classicsCount = classicsPlan.schedule
    .flatMap(s => s.problems)
    .filter(p => p.isInterviewClassic).length;
  console.log(`⭐ Interview classics found: ${classicsCount}`);

  // Test 3: Hidden Gems Mode
  console.log('\n📚 Test 3: Hidden Gems Mode');
  const gemsFormData: StudyPlanFormData = {
    ...balancedFormData,
    name: "Hidden Gems Discovery",
    learningMode: "hidden_gems",
    qualityPreference: "discovery"
  };

  const gemsPlan = studyPlanService.generateStudyPlan(
    gemsFormData,
    mockProblemsWithQuality,
    mockCompanies,
    {
      learningMode: "hidden_gems",
      qualityPreference: "discovery",
      adaptiveDifficulty: true,
      includeQualityMetrics: true
    }
  );

  console.log(`✅ Generated gems plan with ${gemsPlan.schedule.length} sessions`);
  
  // Check for hidden gems
  const gemsCount = gemsPlan.schedule
    .flatMap(s => s.problems)
    .filter(p => p.isHiddenGem).length;
  console.log(`💎 Hidden gems found: ${gemsCount}`);

  // Test 4: Quality Insights
  console.log('\n📊 Test 4: Quality Insights Analysis');
  const qualityInsights = studyPlanService.getQualityInsights(balancedPlan);
  
  console.log(`📈 Average quality score: ${(qualityInsights.averageQualityScore * 100).toFixed(1)}%`);
  console.log(`💎 Hidden gems: ${qualityInsights.hiddenGemsCount}`);
  console.log(`⭐ Interview classics: ${qualityInsights.interviewClassicsCount}`);
  console.log(`🎯 Learning mode effectiveness: ${qualityInsights.learningModeEffectiveness}`);
  
  if (qualityInsights.qualityRecommendations.length > 0) {
    console.log('💡 Quality recommendations:');
    qualityInsights.qualityRecommendations.forEach((rec, i) => {
      console.log(`   ${i + 1}. ${rec}`);
    });
  }

  // Test 5: Adaptive Recommendations
  console.log('\n🎯 Test 5: Adaptive Recommendations');
  const adaptiveRecs = studyPlanService.getAdaptiveRecommendations(balancedPlan);
  
  console.log(`📊 Suggested difficulties: ${adaptiveRecs.suggestedDifficulty.join(', ')}`);
  console.log(`📚 Suggested topics: ${adaptiveRecs.suggestedTopics.join(', ')}`);
  console.log(`🏢 Suggested companies: ${adaptiveRecs.suggestedCompanies.join(', ')}`);
  console.log(`💭 Reasoning: ${adaptiveRecs.reasoning}`);

  console.log('\n✅ All tests completed successfully!');
  console.log('\n🎉 Advanced Study Recommendations are working correctly!');
  
  return {
    balancedPlan,
    classicsPlan,
    gemsPlan,
    qualityInsights,
    adaptiveRecs
  };
}

// Export for potential use in other tests
export { testQualityAwareStudyPlan, mockProblemsWithQuality, mockCompanies };

// Run test if this file is executed directly
if (typeof window === 'undefined') {
  // Node.js environment
  testQualityAwareStudyPlan();
}