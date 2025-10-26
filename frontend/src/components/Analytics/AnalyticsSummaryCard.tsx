import React from 'react';
import {
  Card,
  CardContent,
  Typography,
  Box,
  Chip,
  LinearProgress
} from '@mui/material';
import {
  TrendingUp,
  Business,
  Quiz,
  Topic
} from '@mui/icons-material';
import type { AnalyticsSummary } from '../../types/analytics';

interface AnalyticsSummaryCardProps {
  summary: AnalyticsSummary;
}

export const AnalyticsSummaryCard: React.FC<AnalyticsSummaryCardProps> = ({ summary }) => {
  const difficultyDistribution = summary.difficultyDistribution || {};
  const totalDifficultyProblems = Object.values(difficultyDistribution).reduce((a, b) => a + b, 0);

  const StatCard: React.FC<{
    icon: React.ReactNode;
    title: string;
    value: string | number;
    subtitle?: string;
    color?: 'primary' | 'secondary' | 'success' | 'warning';
  }> = ({ icon, title, value, subtitle, color = 'primary' }) => (
    <Card variant="outlined" sx={{ height: '100%' }}>
      <CardContent>
        <Box display="flex" alignItems="center" mb={1}>
          <Box 
            sx={{ 
              p: 1, 
              borderRadius: 1, 
              bgcolor: `${color}.light`, 
              color: `${color}.contrastText`,
              mr: 2 
            }}
          >
            {icon}
          </Box>
          <Typography variant="h6" component="div">
            {typeof value === 'number' ? value.toLocaleString() : value}
          </Typography>
        </Box>
        <Typography variant="body2" color="text.secondary" gutterBottom>
          {title}
        </Typography>
        {subtitle && (
          <Typography variant="caption" color="text.secondary">
            {subtitle}
          </Typography>
        )}
      </CardContent>
    </Card>
  );

  return (
    <Card>
      <CardContent>
        <Typography variant="h5" gutterBottom>
          Analytics Overview
        </Typography>
        
        {/* Key Metrics */}
        <Box sx={{ 
          display: 'grid', 
          gridTemplateColumns: { xs: '1fr', sm: 'repeat(2, 1fr)', md: 'repeat(4, 1fr)' }, 
          gap: 3, 
          mb: 3 
        }}>
          <StatCard
            icon={<Business />}
            title="Total Companies"
            value={summary.totalCompanies}
            subtitle="In dataset"
            color="primary"
          />
          
          <StatCard
            icon={<Quiz />}
            title="Total Problems"
            value={summary.totalProblems}
            subtitle={`Avg ${summary.avgProblemsPerCompany.toFixed(1)} per company`}
            color="secondary"
          />
          
          <StatCard
            icon={<Topic />}
            title="Total Topics"
            value={summary.totalTopics}
            subtitle="Unique topics covered"
            color="success"
          />
          
          <StatCard
            icon={<TrendingUp />}
            title="Timeframes"
            value={summary.timeframeCoverage.length}
            subtitle="Coverage periods"
            color="warning"
          />
        </Box>

        {/* Difficulty Distribution and Top Companies */}
        <Box sx={{ 
          display: 'grid', 
          gridTemplateColumns: { xs: '1fr', md: 'repeat(2, 1fr)' }, 
          gap: 3, 
          mb: 3 
        }}>
          {/* Difficulty Distribution */}
          <Card variant="outlined">
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Difficulty Distribution
              </Typography>
              <Box sx={{ mt: 2 }}>
                {Object.entries(difficultyDistribution).map(([difficulty, count]) => {
                  const percentage = totalDifficultyProblems > 0 ? (count / totalDifficultyProblems) * 100 : 0;
                  const color = {
                    EASY: 'success',
                    MEDIUM: 'warning', 
                    HARD: 'error',
                    UNKNOWN: 'primary'
                  }[difficulty] as 'success' | 'warning' | 'error' | 'primary';

                  return (
                    <Box key={difficulty} sx={{ mb: 2 }}>
                      <Box display="flex" justifyContent="space-between" alignItems="center" mb={0.5}>
                        <Typography variant="body2">
                          {difficulty}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          {count.toLocaleString()} ({percentage.toFixed(1)}%)
                        </Typography>
                      </Box>
                      <LinearProgress 
                        variant="determinate" 
                        value={percentage} 
                        color={color}
                        sx={{ height: 8, borderRadius: 4 }}
                      />
                    </Box>
                  );
                })}
              </Box>
            </CardContent>
          </Card>

          {/* Top Companies */}
          <Card variant="outlined">
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Top Companies by Problems
              </Typography>
              <Box sx={{ mt: 2 }}>
                {summary.topCompanies.slice(0, 8).map((company, index) => (
                  <Box 
                    key={company.company} 
                    display="flex" 
                    justifyContent="space-between" 
                    alignItems="center"
                    sx={{ 
                      py: 1, 
                      borderBottom: index < 7 ? '1px solid' : 'none',
                      borderColor: 'divider'
                    }}
                  >
                    <Box display="flex" alignItems="center">
                      <Chip 
                        label={`#${company.rank || index + 1}`} 
                        size="small" 
                        sx={{ mr: 1, minWidth: 40 }}
                      />
                      <Typography variant="body2">
                        {company.company}
                      </Typography>
                    </Box>
                    <Typography variant="body2" color="text.secondary">
                      {company.problemCount.toLocaleString()}
                    </Typography>
                  </Box>
                ))}
              </Box>
            </CardContent>
          </Card>
        </Box>

        {/* Top Topics */}
        <Card variant="outlined">
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Most Popular Topics
            </Typography>
            <Box display="flex" flexWrap="wrap" gap={1} mt={2}>
              {summary.topTopics.slice(0, 15).map((topic, index) => (
                <Chip
                  key={topic.topic}
                  label={`${topic.topic} (${topic.frequency})`}
                  variant={index < 5 ? 'filled' : 'outlined'}
                  color={index < 3 ? 'primary' : index < 5 ? 'secondary' : 'default'}
                  size="small"
                />
              ))}
            </Box>
            <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
              Numbers in parentheses show frequency across companies
            </Typography>
          </CardContent>
        </Card>
      </CardContent>
    </Card>
  );
};