import React from 'react';
import {
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend
} from 'recharts';
import { Box, Typography, Paper } from '@mui/material';
import type { QualityDistributionData } from '../../types/analytics';

interface QualityDistributionChartProps {
  data: QualityDistributionData[];
  title?: string;
  height?: number;
}

const CATEGORY_COLORS = {
  'hidden-gem': '#4CAF50',      // Green
  'rising-star': '#2196F3',     // Blue
  'interview-classic': '#FF9800', // Orange
  'controversial': '#F44336',    // Red
  'standard': '#9E9E9E'         // Gray
};

const CATEGORY_LABELS = {
  'hidden-gem': 'Hidden Gems',
  'rising-star': 'Rising Stars',
  'interview-classic': 'Interview Classics',
  'controversial': 'Controversial',
  'standard': 'Standard'
};

const CustomTooltip = ({ active, payload }: any) => {
  if (active && payload && payload.length) {
    const data = payload[0].payload;
    return (
      <Paper sx={{ p: 2, maxWidth: 300 }}>
        <Typography variant="subtitle2" gutterBottom>
          {CATEGORY_LABELS[data.category as keyof typeof CATEGORY_LABELS]}
        </Typography>
        <Typography variant="body2">
          Originality Score: {(data.originalityScore * 100).toFixed(1)}%
        </Typography>
        <Typography variant="body2">
          Total Votes: {data.totalVotes.toLocaleString()}
        </Typography>
        <Typography variant="body2">
          Problems: {data.count}
        </Typography>
      </Paper>
    );
  }
  return null;
};

export const QualityDistributionChart: React.FC<QualityDistributionChartProps> = ({
  data,
  title = "Problem Quality Distribution",
  height = 400
}) => {
  // Group data by category for better visualization
  const categoryData = Object.entries(CATEGORY_COLORS).map(([category, color]) => {
    const categoryProblems = data.filter(d => d.category === category);
    return {
      category,
      color,
      data: categoryProblems
    };
  }).filter(item => item.data.length > 0);

  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        {title}
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
        Originality Score vs Total Votes (bubble size = problem count)
      </Typography>
      
      <ResponsiveContainer width="100%" height={height}>
        <ScatterChart margin={{ top: 20, right: 30, bottom: 60, left: 60 }}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis 
            type="number" 
            dataKey="originalityScore"
            domain={[0.4, 1]}
            tickFormatter={(value) => `${(value * 100).toFixed(0)}%`}
            label={{ value: 'Originality Score', position: 'insideBottom', offset: -10 }}
          />
          <YAxis 
            type="number" 
            dataKey="totalVotes"
            scale="log"
            domain={['dataMin', 'dataMax']}
            tickFormatter={(value) => value.toLocaleString()}
            label={{ value: 'Total Votes (log scale)', angle: -90, position: 'insideLeft' }}
          />
          <Tooltip content={<CustomTooltip />} />
          <Legend />
          
          {categoryData.map(({ category, color, data: categoryProblems }) => (
            <Scatter
              key={category}
              name={CATEGORY_LABELS[category as keyof typeof CATEGORY_LABELS]}
              data={categoryProblems}
              fill={color}
            />
          ))}
        </ScatterChart>
      </ResponsiveContainer>
      
      <Box sx={{ mt: 2, display: 'flex', flexWrap: 'wrap', gap: 1 }}>
        <Typography variant="caption" color="text.secondary">
          Categories: Hidden Gems (high quality, low exposure) • Rising Stars (new, high quality) • 
          Interview Classics (high likes, high exposure) • Controversial (low originality)
        </Typography>
      </Box>
    </Box>
  );
};

export default QualityDistributionChart;