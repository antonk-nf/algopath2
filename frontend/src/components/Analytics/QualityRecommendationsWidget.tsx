import React, { useMemo } from 'react';
import {
  Box,
  Typography,
  Paper,
  Card,
  CardContent,
  CardActions,
  Button,
  Chip,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Divider,
  Alert,
  LinearProgress
} from '@mui/material';
import {
  Diamond as DiamondIcon,
  Star as StarIcon,
  TrendingUp as TrendingUpIcon,
  Recommend as RecommendIcon
} from '@mui/icons-material';
import type { ProblemData } from '../../types';

interface QualityRecommendationsWidgetProps {
  problems: ProblemData[];
  userSkillLevel?: 'beginner' | 'intermediate' | 'advanced';
  targetCompanies?: string[];
  focusTopics?: string[];
  maxRecommendations?: number;
}

interface RecommendationCategory {
  title: string;
  description: string;
  icon: React.ReactNode;
  color: string;
  problems: ProblemData[];
  reasoning: string;
}

const getQualityScore = (problem: ProblemData): number => {
  if (!problem.originalityScore || !problem.likes || !problem.totalVotes) {
    return 0;
  }
  
  // Composite quality score considering multiple factors
  const originalityWeight = 0.4;
  const likesWeight = 0.3;
  const exposureWeight = 0.2; // Lower exposure can be good for hidden gems
  const acceptanceWeight = 0.1;
  
  const normalizedLikes = Math.min(problem.likes / 1000, 1); // Normalize to 0-1
  const exposureScore = 1 - Math.min(problem.totalVotes / 10000, 1); // Inverse - lower is better for gems
  const acceptanceScore = problem.acceptanceRate || 0.5;
  
  return (
    problem.originalityScore * originalityWeight +
    normalizedLikes * likesWeight +
    exposureScore * exposureWeight +
    acceptanceScore * acceptanceWeight
  );
};

const getDifficultyScore = (difficulty: string): number => {
  switch (difficulty) {
    case 'EASY': return 1;
    case 'MEDIUM': return 2;
    case 'HARD': return 3;
    default: return 2;
  }
};

const getSkillLevelRange = (skillLevel: string): [number, number] => {
  switch (skillLevel) {
    case 'beginner': return [1, 2]; // Easy to Medium
    case 'intermediate': return [2, 3]; // Medium to Hard
    case 'advanced': return [2, 3]; // Medium to Hard (but focus on quality)
    default: return [1, 3];
  }
};

export const QualityRecommendationsWidget: React.FC<QualityRecommendationsWidgetProps> = ({
  problems,
  userSkillLevel = 'intermediate',
  targetCompanies = [],
  focusTopics = [],
  maxRecommendations = 5
}) => {
  const recommendations = useMemo(() => {
    // Filter problems with quality metrics
    const qualityProblems = problems.filter(p => 
      p.originalityScore && p.likes && p.totalVotes
    );
    
    if (qualityProblems.length === 0) {
      return [];
    }
    
    const [minDifficulty, maxDifficulty] = getSkillLevelRange(userSkillLevel);
    
    // Hidden Gems: High quality, low exposure
    const hiddenGems = qualityProblems
      .filter(p => {
        const diffScore = getDifficultyScore(p.difficulty);
        return (
          p.originalityScore! > 0.85 &&
          p.totalVotes! < 2000 &&
          p.likes! > 50 &&
          diffScore >= minDifficulty &&
          diffScore <= maxDifficulty
        );
      })
      .sort((a, b) => getQualityScore(b) - getQualityScore(a))
      .slice(0, maxRecommendations);
    
    // Rising Stars: Newer problems with growing popularity
    const risingStars = qualityProblems
      .filter(p => {
        const diffScore = getDifficultyScore(p.difficulty);
        return (
          p.originalityScore! > 0.8 &&
          p.totalVotes! >= 1000 &&
          p.totalVotes! <= 5000 &&
          p.likes! > 100 &&
          diffScore >= minDifficulty &&
          diffScore <= maxDifficulty
        );
      })
      .sort((a, b) => getQualityScore(b) - getQualityScore(a))
      .slice(0, maxRecommendations);
    
    // Company-Specific Quality Problems
    const companyProblems = targetCompanies.length > 0 
      ? qualityProblems
          .filter(p => {
            const diffScore = getDifficultyScore(p.difficulty);
            return (
              p.company &&
              targetCompanies.includes(p.company) &&
              p.originalityScore! > 0.75 &&
              diffScore >= minDifficulty &&
              diffScore <= maxDifficulty
            );
          })
          .sort((a, b) => getQualityScore(b) - getQualityScore(a))
          .slice(0, maxRecommendations)
      : [];
    
    // Topic-Specific Quality Problems
    const topicProblems = focusTopics.length > 0
      ? qualityProblems
          .filter(p => {
            const diffScore = getDifficultyScore(p.difficulty);
            const hasMatchingTopic = p.topics?.some(topic => 
              focusTopics.some(focusTopic => 
                topic.toLowerCase().includes(focusTopic.toLowerCase())
              )
            );
            return (
              hasMatchingTopic &&
              p.originalityScore! > 0.75 &&
              diffScore >= minDifficulty &&
              diffScore <= maxDifficulty
            );
          })
          .sort((a, b) => getQualityScore(b) - getQualityScore(a))
          .slice(0, maxRecommendations)
      : [];
    
    const categories: RecommendationCategory[] = [];
    
    if (hiddenGems.length > 0) {
      categories.push({
        title: 'Hidden Gems',
        description: 'High-quality problems with low exposure - perfect for discovering new challenges',
        icon: <DiamondIcon />,
        color: '#4CAF50',
        problems: hiddenGems,
        reasoning: `Found ${hiddenGems.length} problems with >85% originality and <2K votes`
      });
    }
    
    if (risingStars.length > 0) {
      categories.push({
        title: 'Rising Stars',
        description: 'Newer problems gaining popularity in the community',
        icon: <StarIcon />,
        color: '#2196F3',
        problems: risingStars,
        reasoning: `Found ${risingStars.length} problems with growing community engagement`
      });
    }
    
    if (companyProblems.length > 0) {
      categories.push({
        title: 'Company Focus',
        description: `Quality problems from your target companies: ${targetCompanies.join(', ')}`,
        icon: <TrendingUpIcon />,
        color: '#FF9800',
        problems: companyProblems,
        reasoning: `Found ${companyProblems.length} high-quality problems from target companies`
      });
    }
    
    if (topicProblems.length > 0) {
      categories.push({
        title: 'Topic Mastery',
        description: `Quality problems in your focus areas: ${focusTopics.join(', ')}`,
        icon: <RecommendIcon />,
        color: '#9C27B0',
        problems: topicProblems,
        reasoning: `Found ${topicProblems.length} high-quality problems in focus topics`
      });
    }
    
    return categories;
  }, [problems, userSkillLevel, targetCompanies, focusTopics, maxRecommendations]);
  
  if (recommendations.length === 0) {
    return (
      <Paper sx={{ p: 3 }}>
        <Typography variant="h6" gutterBottom>
          Quality Recommendations
        </Typography>
        <Alert severity="info">
          No quality recommendations available. This could be because:
          <ul>
            <li>Problems don't have quality metrics (likes, originality scores)</li>
            <li>No problems match your skill level and preferences</li>
            <li>Try adjusting your target companies or focus topics</li>
          </ul>
        </Alert>
      </Paper>
    );
  }
  
  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        Quality-Based Recommendations
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        Personalized problem suggestions based on community quality metrics and your preferences
      </Typography>
      
      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
        {recommendations.map((category, index) => (
          <Card key={index} sx={{ border: `2px solid ${category.color}20` }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                <Box sx={{ color: category.color }}>
                  {category.icon}
                </Box>
                <Typography variant="h6" sx={{ color: category.color }}>
                  {category.title}
                </Typography>
                <Chip 
                  label={`${category.problems.length} problems`} 
                  size="small" 
                  sx={{ ml: 'auto' }}
                />
              </Box>
              
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                {category.description}
              </Typography>
              
              <Typography variant="caption" color="text.secondary" sx={{ mb: 2, display: 'block' }}>
                {category.reasoning}
              </Typography>
              
              <List dense>
                {category.problems.map((problem, problemIndex) => (
                  <React.Fragment key={problem.title}>
                    <ListItem sx={{ px: 0 }}>
                      <ListItemIcon sx={{ minWidth: 36 }}>
                        <Box
                          sx={{
                            width: 24,
                            height: 24,
                            borderRadius: '50%',
                            backgroundColor: category.color,
                            color: 'white',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            fontSize: '0.75rem',
                            fontWeight: 'bold'
                          }}
                        >
                          {problemIndex + 1}
                        </Box>
                      </ListItemIcon>
                      <ListItemText
                        primary={
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flexWrap: 'wrap' }}>
                            <Typography variant="subtitle2">
                              {problem.title}
                            </Typography>
                            <Chip 
                              label={problem.difficulty} 
                              size="small"
                              color={
                                problem.difficulty === 'EASY' ? 'success' :
                                problem.difficulty === 'MEDIUM' ? 'warning' :
                                problem.difficulty === 'HARD' ? 'error' : 'default'
                              }
                            />
                            {problem.company && (
                              <Chip label={problem.company} size="small" variant="outlined" />
                            )}
                          </Box>
                        }
                        secondary={
                          <Box sx={{ mt: 0.5 }}>
                            <Box sx={{ display: 'flex', gap: 2, mb: 0.5 }}>
                              <Typography variant="caption">
                                Originality: {((problem.originalityScore || 0) * 100).toFixed(1)}%
                              </Typography>
                              <Typography variant="caption">
                                Likes: {(problem.likes || 0).toLocaleString()}
                              </Typography>
                              <Typography variant="caption">
                                Quality Score: {getQualityScore(problem).toFixed(2)}
                              </Typography>
                            </Box>
                            <LinearProgress 
                              variant="determinate" 
                              value={getQualityScore(problem) * 100}
                              sx={{ height: 4, borderRadius: 2 }}
                            />
                          </Box>
                        }
                      />
                    </ListItem>
                    {problemIndex < category.problems.length - 1 && <Divider />}
                  </React.Fragment>
                ))}
              </List>
            </CardContent>
            
            <CardActions>
              <Button size="small" sx={{ color: category.color }}>
                View All {category.title}
              </Button>
              <Button size="small" variant="outlined">
                Add to Study Plan
              </Button>
            </CardActions>
          </Card>
        ))}
      </Box>
    </Box>
  );
};

export default QualityRecommendationsWidget;