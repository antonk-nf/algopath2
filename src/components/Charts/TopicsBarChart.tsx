import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { Box, Typography, useTheme } from '@mui/material';
import type { CompanyData } from '../../types/company';

interface TopicsBarChartProps {
  company: CompanyData;
  height?: number;
  maxTopics?: number;
}

export function TopicsBarChart({ 
  company, 
  height = 300, 
  maxTopics = 10 
}: TopicsBarChartProps) {
  const theme = useTheme();

  // For now, we'll create mock frequency data since the API doesn't provide topic frequencies
  // In a real implementation, this would come from a separate API endpoint
  const topicsData = company.topTopics
    .slice(0, maxTopics)
    .map((topic, index) => ({
      topic: topic.length > 15 ? `${topic.substring(0, 15)}...` : topic,
      fullTopic: topic,
      frequency: Math.max(1, Math.floor(Math.random() * 20) + (maxTopics - index)) // Mock data
    }))
    .sort((a, b) => b.frequency - a.frequency);

  // Custom tooltip
  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <Box
          sx={{
            backgroundColor: 'background.paper',
            border: 1,
            borderColor: 'divider',
            borderRadius: 1,
            p: 1.5,
            boxShadow: 2,
            maxWidth: 200
          }}
        >
          <Typography variant="body2" sx={{ fontWeight: 'bold', mb: 0.5 }}>
            {data.fullTopic}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Frequency: {data.frequency}
          </Typography>
        </Box>
      );
    }
    return null;
  };

  if (!company.topTopics || company.topTopics.length === 0) {
    return (
      <Box 
        sx={{ 
          height, 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'center' 
        }}
      >
        <Typography variant="body2" color="text.secondary">
          No topic data available
        </Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ width: '100%', height }}>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart
          data={topicsData}
          margin={{
            top: 20,
            right: 30,
            left: 20,
            bottom: 60
          }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke={theme.palette.divider} />
          <XAxis 
            dataKey="topic" 
            angle={-45}
            textAnchor="end"
            height={60}
            fontSize={12}
            stroke={theme.palette.text.secondary}
          />
          <YAxis 
            fontSize={12}
            stroke={theme.palette.text.secondary}
          />
          <Tooltip content={<CustomTooltip />} />
          <Bar 
            dataKey="frequency" 
            fill={theme.palette.primary.main}
            radius={[4, 4, 0, 0]}
          />
        </BarChart>
      </ResponsiveContainer>
    </Box>
  );
}