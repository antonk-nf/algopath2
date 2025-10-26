import React from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Chip,
  Button,
  Paper
} from '@mui/material';
import {
  Business as CompanyIcon,
  TrendingUp as TrendingIcon,
  School as StudyIcon,
  Analytics as AnalyticsIcon,
  Star as StarIcon,
  Speed as SpeedIcon,
  Lightbulb as LightbulbIcon,
  Timeline as TimelineIcon
} from '@mui/icons-material';

interface Feature {
  title: string;
  description: string;
  icon: React.ReactNode;
  benefits: string[];
  status: 'available' | 'beta' | 'coming-soon';
  path?: string;
}

const features: Feature[] = [
  {
    title: 'Company Research',
    description: 'Deep dive into company-specific interview patterns with real data from 470+ companies.',
    icon: <CompanyIcon sx={{ fontSize: 32, color: 'primary.main' }} />,
    benefits: [
      'Company-specific statistics',
      'Difficulty distributions',
      'Topic frequency analysis',
      'FAANG comparisons'
    ],
    status: 'available',
    path: '/company-research'
  },
  {
    title: 'Topic Analysis',
    description: 'Identify trending topics and understand skill demand across the industry.',
    icon: <TrendingIcon sx={{ fontSize: 32, color: 'success.main' }} />,
    benefits: [
      'Real-time topic trends',
      'Cross-company analysis',
      'Skill gap identification',
      'Topic correlations'
    ],
    status: 'available',
    path: '/topic-analysis'
  },
  {
    title: 'Smart Study Planner',
    description: 'AI-powered study plans tailored to your target companies and timeline.',
    icon: <StudyIcon sx={{ fontSize: 32, color: 'warning.main' }} />,
    benefits: [
      'Personalized schedules',
      'Progress tracking',
      'Quality recommendations',
      'Adaptive learning'
    ],
    status: 'available',
    path: '/study-planner'
  },
  {
    title: 'Advanced Analytics',
    description: 'Leverage machine learning insights for optimal interview preparation.',
    icon: <AnalyticsIcon sx={{ fontSize: 32, color: 'secondary.main' }} />,
    benefits: [
      'Quality analysis',
      'Hidden gems discovery',
      'Performance predictions',
      'Success correlations'
    ],
    status: 'available',
    path: '/analytics'
  },
  {
    title: 'Quality Insights',
    description: 'Discover high-quality problems using community feedback and engagement data.',
    icon: <StarIcon sx={{ fontSize: 32, color: 'info.main' }} />,
    benefits: [
      'Community ratings',
      'Originality scores',
      'Problem age analysis',
      'Quality filtering'
    ],
    status: 'beta',
    path: '/analytics'
  },
  {
    title: 'Performance Optimization',
    description: 'Smart caching and progressive loading for seamless user experience.',
    icon: <SpeedIcon sx={{ fontSize: 32, color: 'error.main' }} />,
    benefits: [
      'Instant data access',
      'Offline capabilities',
      'Smart prefetching',
      'Error recovery'
    ],
    status: 'available'
  }
];

interface FeatureHighlightsProps {
  onNavigate?: (path: string) => void;
  compact?: boolean;
}

export function FeatureHighlights({ onNavigate, compact = false }: FeatureHighlightsProps) {
  const getStatusColor = (status: Feature['status']) => {
    switch (status) {
      case 'available': return 'success';
      case 'beta': return 'warning';
      case 'coming-soon': return 'default';
      default: return 'default';
    }
  };

  const getStatusLabel = (status: Feature['status']) => {
    switch (status) {
      case 'available': return 'Available';
      case 'beta': return 'Beta';
      case 'coming-soon': return 'Coming Soon';
      default: return '';
    }
  };

  if (compact) {
    return (
      <Paper sx={{ p: 3, mb: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
          <LightbulbIcon color="primary" />
          <Typography variant="h6">
            Key Features
          </Typography>
        </Box>
        
        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2, justifyContent: 'center' }}>
          {features.slice(0, 4).map((feature, index) => (
            <Box key={index} sx={{ flex: '1 1 200px', textAlign: 'center', minWidth: 150 }}>
              {feature.icon}
              <Typography variant="subtitle2" sx={{ mt: 1 }}>
                {feature.title}
              </Typography>
              <Chip 
                label={getStatusLabel(feature.status)}
                color={getStatusColor(feature.status)}
                size="small"
                sx={{ mt: 0.5 }}
              />
            </Box>
          ))}
        </Box>
      </Paper>
    );
  }

  return (
    <Box>
      <Box sx={{ textAlign: 'center', mb: 4 }}>
        <Typography variant="h3" component="h2" gutterBottom>
          Powerful Features for Interview Success
        </Typography>
        <Typography variant="h6" color="text.secondary" sx={{ maxWidth: 600, mx: 'auto' }}>
          Leverage real interview data and advanced analytics to optimize your preparation strategy
        </Typography>
      </Box>

      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 3 }}>
        {features.map((feature, index) => (
          <Box key={index} sx={{ flex: '1 1 350px', minWidth: 300 }}>
            <Card 
              elevation={2}
              sx={{ 
                height: '100%',
                display: 'flex',
                flexDirection: 'column',
                transition: 'transform 0.2s, box-shadow 0.2s',
                '&:hover': {
                  transform: 'translateY(-4px)',
                  boxShadow: 4
                }
              }}
            >
              <CardContent sx={{ flexGrow: 1, p: 3 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
                  {feature.icon}
                  <Box sx={{ flexGrow: 1 }}>
                    <Typography variant="h6" component="h3">
                      {feature.title}
                    </Typography>
                    <Chip 
                      label={getStatusLabel(feature.status)}
                      color={getStatusColor(feature.status)}
                      size="small"
                    />
                  </Box>
                </Box>

                <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                  {feature.description}
                </Typography>

                <Box sx={{ mb: 2 }}>
                  {feature.benefits.map((benefit, benefitIndex) => (
                    <Box 
                      key={benefitIndex}
                      sx={{ 
                        display: 'flex', 
                        alignItems: 'center', 
                        gap: 1, 
                        mb: 0.5 
                      }}
                    >
                      <Box 
                        sx={{ 
                          width: 4, 
                          height: 4, 
                          borderRadius: '50%', 
                          backgroundColor: 'primary.main' 
                        }} 
                      />
                      <Typography variant="body2">
                        {benefit}
                      </Typography>
                    </Box>
                  ))}
                </Box>

                {feature.path && onNavigate && (
                  <Button
                    variant="outlined"
                    size="small"
                    onClick={() => onNavigate(feature.path!)}
                    disabled={feature.status === 'coming-soon'}
                    fullWidth
                  >
                    {feature.status === 'coming-soon' ? 'Coming Soon' : 'Explore'}
                  </Button>
                )}
              </CardContent>
            </Card>
          </Box>
        ))}
      </Box>

      <Box sx={{ textAlign: 'center', mt: 4, p: 3, backgroundColor: 'grey.50', borderRadius: 2 }}>
        <TimelineIcon sx={{ fontSize: 40, color: 'primary.main', mb: 1 }} />
        <Typography variant="h6" gutterBottom>
          Continuous Improvement
        </Typography>
        <Typography variant="body2" color="text.secondary">
          We're constantly adding new features and improving existing ones based on user feedback and the latest interview trends.
        </Typography>
      </Box>
    </Box>
  );
}