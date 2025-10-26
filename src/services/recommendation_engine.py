"""
Quality-Aware Problem Recommendation Engine

This service provides intelligent problem recommendations based on quality metrics,
company preferences, and study goals. It implements various recommendation strategies
including hidden gems discovery, interview classics identification, and quality-based
study plan optimization.
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
import numpy as np
from collections import defaultdict
import math

from .metadata_lookup_service import metadata_lookup_service

logger = logging.getLogger(__name__)


class RecommendationEngine:
    """
    Quality-aware recommendation engine for LeetCode problems.
    
    Features:
    - Hidden gems discovery (high quality, low exposure)
    - Interview classics identification (high likes + company frequency)
    - Quality-based study plan optimization
    - Adaptive difficulty progression
    - Company-specific recommendations with quality weighting
    """
    
    def __init__(self):
        """Initialize the recommendation engine."""
        self.metadata_service = metadata_lookup_service
        logger.info("RecommendationEngine initialized")
    
    def get_hidden_gems_recommendations(self, 
                                      companies: Optional[List[str]] = None,
                                      topics: Optional[List[str]] = None,
                                      min_originality: float = 0.85,
                                      max_total_votes: int = 1000,
                                      limit: int = 20) -> List[Dict[str, Any]]:
        """
        Find hidden gems - high quality problems with low exposure.
        
        Args:
            companies: Filter by specific companies
            topics: Filter by specific topics
            min_originality: Minimum originality score
            max_total_votes: Maximum total votes (to find less exposed problems)
            limit: Maximum number of recommendations
            
        Returns:
            List of hidden gem recommendations with metadata
        """
        if not self.metadata_service.is_ready():
            logger.warning("Metadata service not ready for hidden gems recommendations")
            return []
        
        logger.info(f"Finding hidden gems for companies: {companies}, topics: {topics}")
        
        # Get base hidden gems from metadata processor
        gems = self.metadata_service.processor.find_hidden_gems(
            min_originality=min_originality,
            max_total_votes=max_total_votes,
            limit=limit * 3,  # Get more to filter
            exclude_paid=True
        )
        
        # Filter by companies and topics if specified
        filtered_gems = []
        for gem in gems:
            include = True
            
            # Company filtering would require cross-referencing with main dataset
            # For now, we'll include all gems and let the caller filter
            
            # Topic filtering (if topic_tags are available in metadata)
            if topics and 'topic_tags' in gem:
                gem_topics = [tag.lower() for tag in gem.get('topic_tags', [])]
                topic_match = any(topic.lower() in gem_topics for topic in topics)
                if not topic_match:
                    include = False
            
            if include:
                # Add recommendation score
                gem['recommendation_score'] = self._calculate_gem_score(gem)
                gem['recommendation_reason'] = (
                    f"Hidden gem: {gem['originality_score']:.1%} quality with only "
                    f"{gem['total_votes']} community votes"
                )
                filtered_gems.append(gem)
        
        # Sort by recommendation score and limit
        filtered_gems.sort(key=lambda x: x['recommendation_score'], reverse=True)
        return filtered_gems[:limit]
    
    def get_interview_classics_recommendations(self,
                                            companies: Optional[List[str]] = None,
                                            topics: Optional[List[str]] = None,
                                            min_likes: int = 5000,
                                            limit: int = 20) -> List[Dict[str, Any]]:
        """
        Find interview classics - most essential problems with high community approval.
        
        Args:
            companies: Filter by specific companies
            topics: Filter by specific topics
            min_likes: Minimum number of likes
            limit: Maximum number of recommendations
            
        Returns:
            List of interview classic recommendations with metadata
        """
        if not self.metadata_service.is_ready():
            logger.warning("Metadata service not ready for classics recommendations")
            return []
        
        logger.info(f"Finding interview classics for companies: {companies}, topics: {topics}")
        
        # Get base classics from metadata processor
        classics = self.metadata_service.processor.find_interview_classics(
            min_likes=min_likes,
            limit=limit * 3,  # Get more to filter
            exclude_paid=True
        )
        
        # Filter and enhance
        filtered_classics = []
        for classic in classics:
            include = True
            
            # Topic filtering (if topic_tags are available in metadata)
            if topics and 'topic_tags' in classic:
                classic_topics = [tag.lower() for tag in classic.get('topic_tags', [])]
                topic_match = any(topic.lower() in classic_topics for topic in topics)
                if not topic_match:
                    include = False
            
            if include:
                # Add recommendation score
                classic['recommendation_score'] = self._calculate_classic_score(classic)
                classic['recommendation_reason'] = (
                    f"Interview classic: {classic['likes']:,} likes with "
                    f"{classic['originality_score']:.1%} positive rating"
                )
                filtered_classics.append(classic)
        
        # Sort by recommendation score and limit
        filtered_classics.sort(key=lambda x: x['recommendation_score'], reverse=True)
        return filtered_classics[:limit]
    
    def get_quality_optimized_study_plan(self,
                                       target_companies: List[str],
                                       focus_topics: Optional[List[str]] = None,
                                       skill_level: str = 'intermediate',
                                       duration_weeks: int = 8,
                                       daily_goal: int = 3,
                                       quality_preference: str = 'balanced') -> Dict[str, Any]:
        """
        Generate a quality-optimized study plan.
        
        Args:
            target_companies: Companies to target for interview prep
            focus_topics: Topics to emphasize
            skill_level: beginner, intermediate, or advanced
            duration_weeks: Study duration in weeks
            daily_goal: Problems per day
            quality_preference: balanced, quality_first, classics_first, or discovery
            
        Returns:
            Dictionary with optimized study plan and quality insights
        """
        if not self.metadata_service.is_ready():
            logger.warning("Metadata service not ready for study plan optimization")
            return {
                'error': 'Quality optimization unavailable',
                'fallback': 'Use basic study plan generation'
            }
        
        logger.info(f"Generating quality-optimized study plan for {target_companies}")
        
        total_problems = duration_weeks * 7 * daily_goal
        
        # Define quality strategy
        strategies = {
            'balanced': {
                'classics_ratio': 0.4,
                'gems_ratio': 0.3,
                'rising_ratio': 0.2,
                'random_ratio': 0.1
            },
            'quality_first': {
                'classics_ratio': 0.2,
                'gems_ratio': 0.5,
                'rising_ratio': 0.3,
                'random_ratio': 0.0
            },
            'classics_first': {
                'classics_ratio': 0.6,
                'gems_ratio': 0.2,
                'rising_ratio': 0.1,
                'random_ratio': 0.1
            },
            'discovery': {
                'classics_ratio': 0.2,
                'gems_ratio': 0.4,
                'rising_ratio': 0.4,
                'random_ratio': 0.0
            }
        }
        
        strategy = strategies.get(quality_preference, strategies['balanced'])
        
        # Calculate problem counts for each category
        classics_count = int(total_problems * strategy['classics_ratio'])
        gems_count = int(total_problems * strategy['gems_ratio'])
        rising_count = int(total_problems * strategy['rising_ratio'])
        random_count = total_problems - classics_count - gems_count - rising_count
        
        # Get recommendations for each category
        recommendations = {
            'classics': self.get_interview_classics_recommendations(
                companies=target_companies,
                topics=focus_topics,
                limit=classics_count
            ),
            'hidden_gems': self.get_hidden_gems_recommendations(
                companies=target_companies,
                topics=focus_topics,
                limit=gems_count
            ),
            'rising_stars': self.metadata_service.processor.find_rising_stars(
                limit=rising_count,
                exclude_paid=True
            )
        }
        
        # Create study plan structure
        study_plan = {
            'plan_metadata': {
                'target_companies': target_companies,
                'focus_topics': focus_topics,
                'skill_level': skill_level,
                'duration_weeks': duration_weeks,
                'daily_goal': daily_goal,
                'quality_preference': quality_preference,
                'total_problems': total_problems
            },
            'quality_distribution': {
                'interview_classics': len(recommendations['classics']),
                'hidden_gems': len(recommendations['hidden_gems']),
                'rising_stars': len(recommendations['rising_stars']),
                'strategy_ratios': strategy
            },
            'recommendations': recommendations,
            'quality_insights': self._generate_study_plan_insights(recommendations, skill_level),
            'weekly_schedule': self._create_weekly_schedule(
                recommendations, duration_weeks, daily_goal
            )
        }
        
        logger.info(f"Generated quality-optimized study plan with {total_problems} problems")
        return study_plan
    
    def get_adaptive_difficulty_progression(self,
                                          current_skill_level: str,
                                          target_companies: List[str],
                                          weeks_available: int) -> Dict[str, Any]:
        """
        Create an adaptive difficulty progression plan based on quality metrics.
        
        Args:
            current_skill_level: Current skill level
            target_companies: Target companies
            weeks_available: Available study time
            
        Returns:
            Dictionary with adaptive progression plan
        """
        if not self.metadata_service.is_ready():
            return {'error': 'Quality metrics unavailable for adaptive progression'}
        
        logger.info(f"Creating adaptive difficulty progression for {current_skill_level} level")
        
        # Define progression strategies based on skill level
        progressions = {
            'beginner': {
                'week_1_2': {'easy': 0.8, 'medium': 0.2, 'hard': 0.0},
                'week_3_4': {'easy': 0.6, 'medium': 0.4, 'hard': 0.0},
                'week_5_6': {'easy': 0.4, 'medium': 0.5, 'hard': 0.1},
                'week_7_8': {'easy': 0.3, 'medium': 0.6, 'hard': 0.1},
                'week_9+': {'easy': 0.2, 'medium': 0.6, 'hard': 0.2}
            },
            'intermediate': {
                'week_1_2': {'easy': 0.4, 'medium': 0.6, 'hard': 0.0},
                'week_3_4': {'easy': 0.3, 'medium': 0.6, 'hard': 0.1},
                'week_5_6': {'easy': 0.2, 'medium': 0.6, 'hard': 0.2},
                'week_7_8': {'easy': 0.1, 'medium': 0.6, 'hard': 0.3},
                'week_9+': {'easy': 0.1, 'medium': 0.5, 'hard': 0.4}
            },
            'advanced': {
                'week_1_2': {'easy': 0.2, 'medium': 0.6, 'hard': 0.2},
                'week_3_4': {'easy': 0.1, 'medium': 0.6, 'hard': 0.3},
                'week_5_6': {'easy': 0.1, 'medium': 0.5, 'hard': 0.4},
                'week_7_8': {'easy': 0.0, 'medium': 0.4, 'hard': 0.6},
                'week_9+': {'easy': 0.0, 'medium': 0.3, 'hard': 0.7}
            }
        }
        
        progression = progressions.get(current_skill_level, progressions['intermediate'])
        
        # Create weekly breakdown
        weekly_plan = []
        for week in range(1, weeks_available + 1):
            if week <= 2:
                ratios = progression['week_1_2']
            elif week <= 4:
                ratios = progression['week_3_4']
            elif week <= 6:
                ratios = progression['week_5_6']
            elif week <= 8:
                ratios = progression['week_7_8']
            else:
                ratios = progression['week_9+']
            
            weekly_plan.append({
                'week': week,
                'difficulty_ratios': ratios,
                'quality_focus': self._get_weekly_quality_focus(week, current_skill_level),
                'recommended_strategies': self._get_weekly_strategies(week, current_skill_level)
            })
        
        return {
            'skill_level': current_skill_level,
            'target_companies': target_companies,
            'weeks_available': weeks_available,
            'progression_plan': weekly_plan,
            'quality_guidelines': self._get_quality_guidelines(current_skill_level),
            'success_metrics': self._get_success_metrics(current_skill_level)
        }
    
    def _calculate_gem_score(self, gem: Dict[str, Any]) -> float:
        """Calculate recommendation score for hidden gems."""
        originality = gem.get('originality_score', 0.5)
        total_votes = gem.get('total_votes', 1000)
        engagement = gem.get('engagement_score', 0.0)
        
        # Higher score for high originality, low votes, good engagement
        score = (
            originality * 0.5 +
            (1 - min(total_votes / 1000, 1.0)) * 0.3 +
            engagement * 0.2
        )
        return score
    
    def _calculate_classic_score(self, classic: Dict[str, Any]) -> float:
        """Calculate recommendation score for interview classics."""
        likes = classic.get('likes', 0)
        originality = classic.get('originality_score', 0.5)
        total_votes = classic.get('total_votes', 1)
        
        # Higher score for high likes, good originality, established problems
        score = (
            min(likes / 10000, 1.0) * 0.4 +
            originality * 0.4 +
            min(total_votes / 5000, 1.0) * 0.2
        )
        return score
    
    def _generate_study_plan_insights(self, recommendations: Dict[str, List], skill_level: str) -> List[Dict[str, Any]]:
        """Generate insights for the study plan."""
        insights = []
        
        # Quality distribution insight
        total_problems = sum(len(recs) for recs in recommendations.values())
        if total_problems > 0:
            classics_pct = len(recommendations['classics']) / total_problems * 100
            gems_pct = len(recommendations['hidden_gems']) / total_problems * 100
            
            insights.append({
                'type': 'quality_distribution',
                'title': 'Quality-Optimized Mix',
                'description': f"{classics_pct:.0f}% interview classics, {gems_pct:.0f}% hidden gems",
                'recommendation': 'This mix balances proven interview problems with high-quality discoveries'
            })
        
        # Skill level insight
        if skill_level == 'beginner':
            insights.append({
                'type': 'skill_guidance',
                'title': 'Beginner-Friendly Approach',
                'description': 'Focus on understanding patterns in high-quality problems',
                'recommendation': 'Start with classics to build confidence, then explore gems'
            })
        elif skill_level == 'advanced':
            insights.append({
                'type': 'skill_guidance',
                'title': 'Advanced Challenge',
                'description': 'Emphasis on hidden gems and complex problem patterns',
                'recommendation': 'Use gems to discover unique approaches and edge cases'
            })
        
        return insights
    
    def _create_weekly_schedule(self, recommendations: Dict[str, List], weeks: int, daily_goal: int) -> List[Dict[str, Any]]:
        """Create a weekly schedule distributing problems optimally."""
        schedule = []
        
        # Flatten all recommendations
        all_problems = []
        for category, problems in recommendations.items():
            for problem in problems:
                problem['category'] = category
                all_problems.append(problem)
        
        # Distribute problems across weeks
        problems_per_week = daily_goal * 7
        
        for week in range(1, weeks + 1):
            start_idx = (week - 1) * problems_per_week
            end_idx = min(start_idx + problems_per_week, len(all_problems))
            
            week_problems = all_problems[start_idx:end_idx]
            
            # Group by category for the week
            week_by_category = defaultdict(list)
            for problem in week_problems:
                week_by_category[problem['category']].append(problem)
            
            schedule.append({
                'week': week,
                'total_problems': len(week_problems),
                'by_category': dict(week_by_category),
                'daily_breakdown': self._create_daily_breakdown(week_problems, daily_goal)
            })
        
        return schedule
    
    def _create_daily_breakdown(self, week_problems: List[Dict], daily_goal: int) -> List[Dict[str, Any]]:
        """Create daily breakdown for a week's problems."""
        daily_schedule = []
        
        for day in range(1, 8):  # 7 days
            start_idx = (day - 1) * daily_goal
            end_idx = min(start_idx + daily_goal, len(week_problems))
            
            day_problems = week_problems[start_idx:end_idx]
            
            daily_schedule.append({
                'day': day,
                'problems': day_problems,
                'count': len(day_problems),
                'categories': list(set(p['category'] for p in day_problems))
            })
        
        return daily_schedule
    
    def _get_weekly_quality_focus(self, week: int, skill_level: str) -> str:
        """Get quality focus for a specific week."""
        if week <= 2:
            return 'Foundation building with proven classics'
        elif week <= 4:
            return 'Pattern recognition with quality problems'
        elif week <= 6:
            return 'Exploring hidden gems and unique approaches'
        else:
            return 'Advanced problem solving and optimization'
    
    def _get_weekly_strategies(self, week: int, skill_level: str) -> List[str]:
        """Get recommended strategies for a specific week."""
        base_strategies = [
            'Focus on understanding problem patterns',
            'Practice explaining solutions clearly',
            'Time yourself on each problem'
        ]
        
        if week <= 2:
            base_strategies.append('Master fundamental data structures')
        elif week <= 4:
            base_strategies.append('Learn common algorithmic patterns')
        elif week <= 6:
            base_strategies.append('Explore edge cases and optimizations')
        else:
            base_strategies.append('Practice system design integration')
        
        return base_strategies
    
    def _get_quality_guidelines(self, skill_level: str) -> List[str]:
        """Get quality guidelines based on skill level."""
        guidelines = [
            'Prioritize problems with high originality scores (>0.8)',
            'Balance classics (high likes) with hidden gems (low exposure)',
            'Focus on problems with official solutions when learning'
        ]
        
        if skill_level == 'beginner':
            guidelines.extend([
                'Start with problems having >70% acceptance rates',
                'Avoid controversial problems (low originality scores)'
            ])
        elif skill_level == 'advanced':
            guidelines.extend([
                'Challenge yourself with low acceptance rate problems',
                'Explore problems with unique approaches (hidden gems)'
            ])
        
        return guidelines
    
    def _get_success_metrics(self, skill_level: str) -> Dict[str, Any]:
        """Get success metrics based on skill level."""
        base_metrics = {
            'completion_rate': 0.8,
            'understanding_depth': 'Can explain solution approach',
            'time_management': 'Complete within 2x optimal time'
        }
        
        if skill_level == 'beginner':
            base_metrics.update({
                'target_acceptance_rate': 0.6,
                'focus_areas': ['Arrays', 'Strings', 'Hash Tables']
            })
        elif skill_level == 'advanced':
            base_metrics.update({
                'target_acceptance_rate': 0.4,
                'focus_areas': ['Dynamic Programming', 'Graph Algorithms', 'System Design']
            })
        
        return base_metrics


# Global instance
recommendation_engine = RecommendationEngine()