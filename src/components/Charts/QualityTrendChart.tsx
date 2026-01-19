import React from 'react';
import {
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
  ComposedChart,
  Bar
} from 'recharts';
import { Box, Typography, Paper } from '@mui/material';
import type { QualityTrendData } from '../../types/analytics';

interface QualityTrendChartProps {
  data: QualityTrendData[];
  title?: string;
  height?: number;
}

const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    return (
      <Paper sx={{ p: 2, maxWidth: 300 }}>
        <Typography variant="subtitle2" gutterBottom>
          {label}
        </Typography>
        {payload.map((entry: any, index: number) => (
          <Typography key={index} variant="body2" sx={{ color: entry.color }}>
            {entry.name}: {
              entry.dataKey === 'avgOriginalityScore' 
                ? `${(entry.value * 100).toFixed(1)}%`
                : entry.value.toLocaleString()
            }
          </Typography>
        ))}
      </Paper>
    );
  }
  return null;
};

export const QualityTrendChart: React.FC<QualityTrendChartProps> = ({
  data,
  title = "Problem Quality Trends Over Time",
  height = 400
}) => {
  // Sort data by timeframe for proper chronological order
  const sortedData = [...data].sort((a, b) => {
    // Simple sorting - assumes timeframes like "30d", "3m", "6m", "1y"
    const getTimeValue = (timeframe: string) => {
      if (timeframe.includes('d')) return parseInt(timeframe);
      if (timeframe.includes('m')) return parseInt(timeframe) * 30;
      if (timeframe.includes('y')) return parseInt(timeframe) * 365;
      return 0;
    };
    return getTimeValue(a.timeframe) - getTimeValue(b.timeframe);
  });

  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        {title}
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
        Track how problem quality metrics change over different time periods
      </Typography>
      
      <ResponsiveContainer width="100%" height={height}>
        <ComposedChart data={sortedData} margin={{ top: 20, right: 30, bottom: 20, left: 20 }}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis 
            dataKey="timeframe" 
            label={{ value: 'Time Period', position: 'insideBottom', offset: -10 }}
          />
          <YAxis 
            yAxisId="left"
            tickFormatter={(value) => `${(value * 100).toFixed(0)}%`}
            label={{ value: 'Quality Score (%)', angle: -90, position: 'insideLeft' }}
          />
          <YAxis 
            yAxisId="right" 
            orientation="right"
            label={{ value: 'Problem Count', angle: 90, position: 'insideRight' }}
          />
          <Tooltip content={<CustomTooltip />} />
          <Legend />
          
          {/* Quality metrics as lines */}
          <Line
            yAxisId="left"
            type="monotone"
            dataKey="avgOriginalityScore"
            stroke="#2196F3"
            strokeWidth={3}
            name="Avg Originality Score"
            dot={{ fill: '#2196F3', strokeWidth: 2, r: 4 }}
          />
          
          {/* Problem counts as bars */}
          <Bar
            yAxisId="right"
            dataKey="newProblemsCount"
            fill="#4CAF50"
            fillOpacity={0.6}
            name="New Problems"
          />
          <Bar
            yAxisId="right"
            dataKey="qualityProblemsCount"
            fill="#FF9800"
            fillOpacity={0.6}
            name="Quality Problems (>80%)"
          />
        </ComposedChart>
      </ResponsiveContainer>
      
      <Box sx={{ mt: 2, display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 2 }}>
        <Paper sx={{ p: 2 }}>
          <Typography variant="subtitle2" color="primary">
            Quality Trend
          </Typography>
          <Typography variant="body2" color="text.secondary">
            {data.length > 1 && (
              <>
                {data[data.length - 1].avgOriginalityScore > data[0].avgOriginalityScore 
                  ? "📈 Improving quality over time"
                  : "📉 Declining quality over time"
                }
              </>
            )}
          </Typography>
        </Paper>
        
        <Paper sx={{ p: 2 }}>
          <Typography variant="subtitle2" color="success.main">
            New Problems
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Total: {data.reduce((sum, d) => sum + d.newProblemsCount, 0).toLocaleString()}
          </Typography>
        </Paper>
        
        <Paper sx={{ p: 2 }}>
          <Typography variant="subtitle2" color="warning.main">
            Quality Problems
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Total: {data.reduce((sum, d) => sum + d.qualityProblemsCount, 0).toLocaleString()}
          </Typography>
        </Paper>
      </Box>
    </Box>
  );
};

export default QualityTrendChart;