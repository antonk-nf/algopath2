
import {
  Card,
  CardContent,
  CardActionArea,
  Typography,
  Box,
  Chip,
  Tooltip
} from '@mui/material';
import {
  Business as BusinessIcon,
  TrendingUp as TrendingUpIcon,
  Assignment as AssignmentIcon
} from '@mui/icons-material';
import type { CompanyData } from '../../types/company';

interface CompanyCardProps {
  company: CompanyData;
  onClick?: (companyName: string) => void;
}

export function CompanyCard({ company, onClick }: CompanyCardProps) {
  const handleClick = () => {
    if (onClick) {
      onClick(company.company);
    }
  };

  // Ensure difficulty distribution exists with default values
  const difficultyDistribution = company.difficultyDistribution || {
    EASY: 0,
    MEDIUM: 0,
    HARD: 0,
    UNKNOWN: 0
  };

  // Calculate difficulty percentages
  const totalDifficultyProblems = 
    difficultyDistribution.EASY +
    difficultyDistribution.MEDIUM +
    difficultyDistribution.HARD +
    difficultyDistribution.UNKNOWN;

  const difficultyPercentages = {
    EASY: totalDifficultyProblems > 0 ? (difficultyDistribution.EASY / totalDifficultyProblems) * 100 : 0,
    MEDIUM: totalDifficultyProblems > 0 ? (difficultyDistribution.MEDIUM / totalDifficultyProblems) * 100 : 0,
    HARD: totalDifficultyProblems > 0 ? (difficultyDistribution.HARD / totalDifficultyProblems) * 100 : 0,
    UNKNOWN: totalDifficultyProblems > 0 ? (difficultyDistribution.UNKNOWN / totalDifficultyProblems) * 100 : 0
  };

  const getDifficultyColor = (difficulty: string) => {
    switch (difficulty) {
      case 'EASY': return '#4caf50';
      case 'MEDIUM': return '#ff9800';
      case 'HARD': return '#f44336';
      default: return '#9e9e9e';
    }
  };

  return (
    <Card 
      sx={{ 
        height: '100%',
        transition: 'all 0.2s ease-in-out',
        '&:hover': {
          transform: 'translateY(-2px)',
          boxShadow: 3
        }
      }}
    >
      <CardActionArea onClick={handleClick} sx={{ height: '100%' }}>
        <CardContent sx={{ p: 3, height: '100%', display: 'flex', flexDirection: 'column' }}>
          {/* Header */}
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
            <BusinessIcon sx={{ mr: 1, color: 'primary.main' }} />
            <Typography variant="h6" component="h3" sx={{ flexGrow: 1, fontWeight: 600 }}>
              {company.company}
            </Typography>
            {company.rank && (
              <Chip 
                label={`#${company.rank}`} 
                size="small" 
                color="primary" 
                variant="outlined"
              />
            )}
          </Box>

          {/* Key Metrics */}
          <Box sx={{ display: 'flex', gap: 2, mb: 2 }}>
            <Box sx={{ textAlign: 'center', flex: 1 }}>
              <Typography variant="h4" color="primary.main" sx={{ fontWeight: 'bold' }}>
                {company.totalProblems}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Total Problems
              </Typography>
            </Box>
            <Box sx={{ textAlign: 'center', flex: 1 }}>
              <Typography variant="h4" color="secondary.main" sx={{ fontWeight: 'bold' }}>
                {company.uniqueProblems}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Unique Problems
              </Typography>
            </Box>
          </Box>

          {/* Frequency and Acceptance Rate */}
          <Box sx={{ mb: 2 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
              <TrendingUpIcon sx={{ mr: 1, fontSize: 16, color: 'text.secondary' }} />
              <Typography variant="body2" color="text.secondary">
                Avg Frequency: <strong>{company.avgFrequency.toFixed(1)}</strong>
              </Typography>
            </Box>
            <Box sx={{ display: 'flex', alignItems: 'center' }}>
              <AssignmentIcon sx={{ mr: 1, fontSize: 16, color: 'text.secondary' }} />
              <Typography variant="body2" color="text.secondary">
                Avg Acceptance: <strong>{(company.avgAcceptanceRate * 100).toFixed(1)}%</strong>
              </Typography>
            </Box>
          </Box>

          {/* Difficulty Distribution */}
          <Box sx={{ mb: 2, flexGrow: 1 }}>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
              Difficulty Distribution
            </Typography>
            <Box sx={{ mb: 1 }}>
              {Object.entries(difficultyPercentages).map(([difficulty, percentage]) => (
                percentage > 0 && (
                  <Tooltip 
                    key={difficulty}
                    title={`${difficulty}: ${difficultyDistribution[difficulty as keyof typeof difficultyDistribution]} problems (${percentage.toFixed(1)}%)`}
                  >
                    <Box
                      sx={{
                        display: 'inline-block',
                        width: `${percentage}%`,
                        height: 8,
                        backgroundColor: getDifficultyColor(difficulty),
                        '&:first-of-type': { borderRadius: '4px 0 0 4px' },
                        '&:last-of-type': { borderRadius: '0 4px 4px 0' },
                        '&:only-of-type': { borderRadius: '4px' }
                      }}
                    />
                  </Tooltip>
                )
              ))}
            </Box>
            <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
              {Object.entries(difficultyDistribution).map(([difficulty, count]) => (
                count > 0 && (
                  <Typography key={difficulty} variant="caption" color="text.secondary">
                    {difficulty}: {count}
                  </Typography>
                )
              ))}
            </Box>
          </Box>

          {/* Top Topics */}
          {company.topTopics && company.topTopics.length > 0 && (
            <Box>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                Top Topics
              </Typography>
              <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
                {company.topTopics.slice(0, 3).map((topic) => (
                  <Chip
                    key={topic}
                    label={topic}
                    size="small"
                    variant="outlined"
                    sx={{ fontSize: '0.75rem' }}
                  />
                ))}
                {company.topTopics.length > 3 && (
                  <Chip
                    label={`+${company.topTopics.length - 3} more`}
                    size="small"
                    variant="outlined"
                    sx={{ fontSize: '0.75rem' }}
                  />
                )}
              </Box>
            </Box>
          )}
        </CardContent>
      </CardActionArea>
    </Card>
  );
}