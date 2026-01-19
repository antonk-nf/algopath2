import React from 'react';
import { Box, Typography, Paper, Tooltip } from '@mui/material';
import type { SentimentHeatmapData } from '../../types/analytics';

interface SentimentHeatmapChartProps {
  data: SentimentHeatmapData[];
  title?: string;
  height?: number;
}

const DIFFICULTY_ORDER = ['EASY', 'MEDIUM', 'HARD', 'UNKNOWN'];

const getSentimentColor = (sentiment: string, intensity: number): string => {
  const alpha = Math.min(Math.max(intensity, 0.2), 1);
  
  switch (sentiment) {
    case 'positive':
      return `rgba(76, 175, 80, ${alpha})`; // Green
    case 'neutral':
      return `rgba(158, 158, 158, ${alpha})`; // Gray
    case 'negative':
      return `rgba(244, 67, 54, ${alpha})`; // Red
    default:
      return `rgba(158, 158, 158, ${alpha})`;
  }
};

const getSentimentIntensity = (avgOriginalityScore: number): number => {
  // Convert originality score (0.4-1.0) to intensity (0.2-1.0)
  return Math.min(Math.max((avgOriginalityScore - 0.4) / 0.6, 0.2), 1);
};

const HeatmapCell: React.FC<{
  data: SentimentHeatmapData;
  maxProblems: number;
}> = ({ data, maxProblems }) => {
  const intensity = getSentimentIntensity(data.avgOriginalityScore);
  const backgroundColor = getSentimentColor(data.sentiment, intensity);
  const cellSize = Math.max(40 + (data.problemCount / maxProblems) * 40, 40);
  
  return (
    <Tooltip
      title={
        <Box>
          <Typography variant="subtitle2">{data.topic}</Typography>
          <Typography variant="body2">Difficulty: {data.difficulty}</Typography>
          <Typography variant="body2">
            Originality: {(data.avgOriginalityScore * 100).toFixed(1)}%
          </Typography>
          <Typography variant="body2">
            Avg Likes: {data.avgLikes.toFixed(1)}
          </Typography>
          <Typography variant="body2">
            Avg Dislikes: {data.avgDislikes.toFixed(1)}
          </Typography>
          <Typography variant="body2">
            Problems: {data.problemCount}
          </Typography>
          <Typography variant="body2">
            Sentiment: {data.sentiment}
          </Typography>
        </Box>
      }
    >
      <Box
        sx={{
          width: cellSize,
          height: cellSize,
          backgroundColor,
          border: '1px solid #e0e0e0',
          borderRadius: 1,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          cursor: 'pointer',
          transition: 'transform 0.2s',
          '&:hover': {
            transform: 'scale(1.05)',
            zIndex: 1,
          }
        }}
      >
        <Typography 
          variant="caption" 
          sx={{ 
            color: intensity > 0.6 ? 'white' : 'black',
            fontWeight: 'bold',
            textAlign: 'center',
            fontSize: '0.7rem'
          }}
        >
          {data.problemCount}
        </Typography>
      </Box>
    </Tooltip>
  );
};

export const SentimentHeatmapChart: React.FC<SentimentHeatmapChartProps> = ({
  data,
  title = "Community Sentiment Heatmap by Topic and Difficulty",
  height = 500
}) => {
  // Group data by topic and difficulty
  const topics = [...new Set(data.map(d => d.topic))].sort();
  const maxProblems = Math.max(...data.map(d => d.problemCount));
  
  // Create a map for quick lookup
  const dataMap = new Map<string, SentimentHeatmapData>();
  data.forEach(item => {
    const key = `${item.topic}-${item.difficulty}`;
    dataMap.set(key, item);
  });

  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        {title}
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
        Cell color intensity = originality score, cell size = problem count, 
        green = positive sentiment, gray = neutral, red = negative
      </Typography>
      
      <Paper sx={{ p: 2, overflow: 'auto', maxHeight: height }}>
        <Box sx={{ display: 'flex', minWidth: 'fit-content' }}>
          {/* Y-axis labels (Topics) */}
          <Box sx={{ display: 'flex', flexDirection: 'column', mr: 2, minWidth: 150 }}>
            <Box sx={{ height: 60 }} /> {/* Header spacer */}
            {topics.map(topic => (
              <Box
                key={topic}
                sx={{
                  height: 60,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'flex-end',
                  pr: 1
                }}
              >
                <Typography variant="caption" sx={{ textAlign: 'right' }}>
                  {topic.length > 20 ? `${topic.substring(0, 17)}...` : topic}
                </Typography>
              </Box>
            ))}
          </Box>
          
          {/* Heatmap grid */}
          <Box>
            {/* X-axis labels (Difficulties) */}
            <Box sx={{ display: 'flex', height: 60, alignItems: 'flex-end', pb: 1 }}>
              {DIFFICULTY_ORDER.map(difficulty => (
                <Box
                  key={difficulty}
                  sx={{
                    width: 80,
                    textAlign: 'center',
                    mx: 0.5
                  }}
                >
                  <Typography variant="caption" fontWeight="bold">
                    {difficulty}
                  </Typography>
                </Box>
              ))}
            </Box>
            
            {/* Heatmap cells */}
            {topics.map(topic => (
              <Box key={topic} sx={{ display: 'flex', height: 60, alignItems: 'center' }}>
                {DIFFICULTY_ORDER.map(difficulty => {
                  const key = `${topic}-${difficulty}`;
                  const cellData = dataMap.get(key);
                  
                  return (
                    <Box
                      key={difficulty}
                      sx={{
                        width: 80,
                        height: 50,
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        mx: 0.5
                      }}
                    >
                      {cellData ? (
                        <HeatmapCell data={cellData} maxProblems={maxProblems} />
                      ) : (
                        <Box
                          sx={{
                            width: 40,
                            height: 40,
                            backgroundColor: '#f5f5f5',
                            border: '1px solid #e0e0e0',
                            borderRadius: 1,
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center'
                          }}
                        >
                          <Typography variant="caption" color="text.disabled">
                            -
                          </Typography>
                        </Box>
                      )}
                    </Box>
                  );
                })}
              </Box>
            ))}
          </Box>
        </Box>
        
        {/* Legend */}
        <Box sx={{ mt: 3, display: 'flex', gap: 4, flexWrap: 'wrap' }}>
          <Box>
            <Typography variant="caption" fontWeight="bold">Sentiment:</Typography>
            <Box sx={{ display: 'flex', gap: 1, mt: 0.5 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                <Box sx={{ width: 16, height: 16, backgroundColor: 'rgba(76, 175, 80, 0.7)', borderRadius: 0.5 }} />
                <Typography variant="caption">Positive</Typography>
              </Box>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                <Box sx={{ width: 16, height: 16, backgroundColor: 'rgba(158, 158, 158, 0.7)', borderRadius: 0.5 }} />
                <Typography variant="caption">Neutral</Typography>
              </Box>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                <Box sx={{ width: 16, height: 16, backgroundColor: 'rgba(244, 67, 54, 0.7)', borderRadius: 0.5 }} />
                <Typography variant="caption">Negative</Typography>
              </Box>
            </Box>
          </Box>
          
          <Box>
            <Typography variant="caption" fontWeight="bold">Intensity:</Typography>
            <Typography variant="caption" display="block">
              Darker = Higher originality score
            </Typography>
          </Box>
          
          <Box>
            <Typography variant="caption" fontWeight="bold">Size:</Typography>
            <Typography variant="caption" display="block">
              Larger = More problems
            </Typography>
          </Box>
        </Box>
      </Paper>
    </Box>
  );
};

export default SentimentHeatmapChart;