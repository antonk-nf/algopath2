import React from 'react';
import {
  Card,
  CardContent,
  Typography,
  Box,
  Chip,
  Alert
} from '@mui/material';
import type { CompanyComparison } from '../../types/analytics';

interface CompanyComparisonChartProps {
  comparison: CompanyComparison;
}

export const CompanyComparisonChart: React.FC<CompanyComparisonChartProps> = ({ comparison }) => {
  const COLORS = ['#8884d8', '#82ca9d', '#ffc658', '#ff7300', '#8dd1e1', '#d084d0'];

  return (
    <Card>
      <CardContent>
        <Typography variant="h5" gutterBottom>
          Company Comparison Analysis
        </Typography>
        
        <Typography variant="body2" color="text.secondary" paragraph>
          Comparing {comparison.companies.length} companies across multiple metrics
        </Typography>

        {/* Company chips */}
        <Box display="flex" flexWrap="wrap" gap={1} mb={3}>
          {comparison.companies.map((company, index) => (
            <Chip
              key={company}
              label={company}
              sx={{ 
                bgcolor: COLORS[index % COLORS.length], 
                color: 'white',
                fontWeight: 'medium'
              }}
            />
          ))}
        </Box>

        {/* Basic Metrics Display */}
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
          {comparison.companies.map((company) => (
            <Card key={company} variant="outlined">
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  {company}
                </Typography>
                <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: 2 }}>
                  <Box>
                    <Typography variant="body2" color="text.secondary">Total Problems</Typography>
                    <Typography variant="h6">{comparison.metrics.totalProblems[company] || 0}</Typography>
                  </Box>
                  <Box>
                    <Typography variant="body2" color="text.secondary">Unique Problems</Typography>
                    <Typography variant="h6">{comparison.metrics.uniqueProblems[company] || 0}</Typography>
                  </Box>
                  <Box>
                    <Typography variant="body2" color="text.secondary">Avg Frequency</Typography>
                    <Typography variant="h6">{(comparison.metrics.avgFrequency[company] || 0).toFixed(2)}</Typography>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          ))}
        </Box>

        {/* Recommendations */}
        {comparison.recommendations && comparison.recommendations.length > 0 && (
          <Box sx={{ mt: 3 }}>
            <Typography variant="h6" gutterBottom>
              Recommendations
            </Typography>
            {comparison.recommendations.map((rec, index) => (
              <Alert key={index} severity="info" sx={{ mb: 2 }}>
                <Typography variant="subtitle2" gutterBottom>
                  {rec.company}
                </Typography>
                <Typography variant="body2" paragraph>
                  {rec.recommendation}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  {rec.reasoning}
                </Typography>
              </Alert>
            ))}
          </Box>
        )}
      </CardContent>
    </Card>
  );
};