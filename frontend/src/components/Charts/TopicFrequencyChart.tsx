import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { Box, Typography, useTheme } from '@mui/material';
import { TrendingUp, TrendingDown, TrendingFlat } from '@mui/icons-material';
import type { TopicFrequency, TopicTrend } from '../../types/topic';

interface TopicFrequencyChartProps {
  data: TopicFrequency[] | TopicTrend[];
  height?: number;
  maxTopics?: number;
  showTrendIndicators?: boolean;
}

export function TopicFrequencyChart({ 
  data, 
  height = 400, 
  maxTopics = 15,
  showTrendIndicators = false
}: TopicFrequencyChartProps) {
  const theme = useTheme();

  // Transform data for the chart
  const chartData = (Array.isArray(data) ? data : [])
    .slice(0, maxTopics)
    .map((item, index) => {
      // Handle both TopicFrequency and TopicTrend types
      const rawFrequency = 'frequency' in item ? item.frequency : (item.totalFrequency ?? 0);
      const frequency = Number.isFinite(rawFrequency) ? Number(rawFrequency) : 0;
      const trendDirection = 'trendDirection' in item ? item.trendDirection : undefined;
      const trendStrength = 'trendStrength' in item ? item.trendStrength : undefined;
      
      return {
        topic: item.topic.length > 20 ? `${item.topic.substring(0, 20)}...` : item.topic,
        fullTopic: item.topic,
        frequency,
        trendDirection,
        trendStrength,
        rank: index + 1
      };
    })
    .sort((a, b) => b.frequency - a.frequency);

  // Get trend icon component
  const getTrendIcon = (direction?: string) => {
    switch ((direction || '').toLowerCase()) {
      case 'increasing':
      case 'up':
      case 'rising':
        return <TrendingUp sx={{ fontSize: 16, color: theme.palette.success.main }} />;
      case 'decreasing':
      case 'down':
      case 'falling':
        return <TrendingDown sx={{ fontSize: 16, color: theme.palette.error.main }} />;
      default:
        return <TrendingFlat sx={{ fontSize: 16, color: theme.palette.action.active }} />;
    }
  };

  // Custom tooltip
  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length && payload[0]?.payload) {
      const datum = payload[0].payload;
      return (
        <Box
          sx={{
            backgroundColor: 'background.paper',
            border: 1,
            borderColor: 'divider',
            borderRadius: 1,
            p: 1.5,
            boxShadow: 2,
            maxWidth: 250
          }}
        >
          <Typography variant="body2" sx={{ fontWeight: 'bold', mb: 0.5 }}>
            #{datum.rank} {datum.fullTopic}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Frequency: {datum.frequency.toLocaleString()}
          </Typography>
          {showTrendIndicators && datum.trendDirection && (
            <Box sx={{ display: 'flex', alignItems: 'center', mt: 0.5 }}>
              {getTrendIcon(datum.trendDirection)}
              <Typography variant="body2" color="text.secondary" sx={{ ml: 0.5 }}>
                {datum.trendDirection} {datum.trendStrength ? `(${(datum.trendStrength * 100).toFixed(1)}%)` : ''}
              </Typography>
            </Box>
          )}
        </Box>
      );
    }
    return null;
  };

  // Custom label for bars (showing trend indicators)
  const CustomLabel = (props: any) => {
    if (!showTrendIndicators || !props) return null;

    const { x = 0, y = 0, width = 0, payload } = props;
    const direction = payload?.trendDirection;

    if (!direction) {
      return null;
    }

    return (
      <g>
        <foreignObject x={x + width - 20} y={y - 10} width={20} height={20}>
          <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
            {getTrendIcon(direction)}
          </div>
        </foreignObject>
      </g>
    );
  };

  if (!data || data.length === 0) {
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
          No topic frequency data available
        </Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ width: '100%', height }}>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart
          data={chartData}
          margin={{
            top: 20,
            right: 30,
            left: 20,
            bottom: 80
          }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke={theme.palette.divider} />
          <XAxis 
            dataKey="topic" 
            angle={-45}
            textAnchor="end"
            height={80}
            fontSize={11}
            stroke={theme.palette.text.secondary}
            interval={0}
          />
          <YAxis 
            fontSize={12}
            stroke={theme.palette.text.secondary}
            tickFormatter={(value) => value.toLocaleString()}
          />
          <Tooltip content={<CustomTooltip />} />
          <Bar 
            dataKey="frequency" 
            fill={theme.palette.primary.main}
            radius={[4, 4, 0, 0]}
            label={showTrendIndicators ? (props: any) => <CustomLabel {...props} /> : undefined}
          />
        </BarChart>
      </ResponsiveContainer>
    </Box>
  );
}
