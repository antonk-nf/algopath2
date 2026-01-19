import { Box, Typography, useTheme, Tooltip, Paper, FormControl, InputLabel, Select, MenuItem } from '@mui/material';
import { useMemo } from 'react';
import type { TopicHeatmap } from '../../types/topic';

interface TopicHeatmapChartProps {
  data: TopicHeatmap;
  height?: number;
  maxTopics?: number;
  maxCompanies?: number;
  colorScheme?: 'viridis' | 'plasma' | 'blues' | 'reds' | 'oranges';
  normalizationMode?: 'absolute' | 'relative';
}

interface HeatmapCell {
  topic: string;
  company: string;
  value: number;
  relativeByTopic?: number;  // What % of this topic belongs to this company
  relativeByCompany?: number; // What % of this company's total is this topic
  normalizedValue: number;
  x: number;
  y: number;
}

// Top companies by problem count from the dataset
const TOP_COMPANIES = [
  'Amazon', 'Meta', 'Google', 'Microsoft', 'Bloomberg',
  'Apple', 'TikTok', 'LinkedIn', 'Uber', 'Oracle',
  'Goldman Sachs', 'Salesforce', 'Nvidia', 'Snap', 'DoorDash',
];

export function TopicHeatmapChart({
  data,
  height = 500,
  maxTopics = 15,
  maxCompanies = 10,
  colorScheme = 'plasma',
  normalizationMode = 'relative'
}: TopicHeatmapChartProps) {
  const theme = useTheme();

  // Process and normalize the heatmap data with relative frequency
  const processedData = useMemo(() => {
    if (!data || !data.matrix || !data.topics || !data.companies) {
      return { cells: [], maxValue: 0, maxRelativeValue: 0, topics: [], companies: [], topicTotals: [] };
    }

    // Limit topics for better visualization
    const limitedTopics = data.topics.slice(0, maxTopics);

    // Use top companies list - filter to only those available in data, preserving order
    const availableCompanies = new Set(data.companies);
    const topAvailable = TOP_COMPANIES.filter(c => availableCompanies.has(c));

    // Use top companies list if enough available, otherwise fall back to sorting by problem count
    let limitedCompanies: string[];
    if (topAvailable.length >= 5) {
      limitedCompanies = topAvailable.slice(0, maxCompanies);
    } else {
      // Fallback: sort by total problems and take top N
      const companyTotalsList = data.companies.map((company, idx) => ({
        company,
        total: data.matrix.reduce((sum, row) => sum + (row[idx] || 0), 0)
      }));
      companyTotalsList.sort((a, b) => b.total - a.total);
      limitedCompanies = companyTotalsList.slice(0, maxCompanies).map(c => c.company);
    }

    // Create mapping from company name to original index in data.companies
    const companyToOriginalIndex = new Map<string, number>();
    data.companies.forEach((company, idx) => {
      companyToOriginalIndex.set(company, idx);
    });

    // Helper to get original index for a company
    const getOriginalCompanyIndex = (company: string): number => {
      return companyToOriginalIndex.get(company) ?? -1;
    };

    // Calculate topic totals (sum across selected companies for each topic)
    const topicTotals: number[] = [];
    limitedTopics.forEach((_, topicIndex) => {
      let topicTotal = 0;
      limitedCompanies.forEach((company) => {
        const originalIdx = getOriginalCompanyIndex(company);
        if (topicIndex < data.matrix.length && originalIdx >= 0 && originalIdx < data.matrix[topicIndex].length) {
          topicTotal += data.matrix[topicIndex][originalIdx] || 0;
        }
      });
      topicTotals.push(topicTotal);
    });

    // Calculate company totals (sum across all topics for each company)
    const companyTotals: number[] = [];
    limitedCompanies.forEach((company) => {
      const originalIdx = getOriginalCompanyIndex(company);
      let companyTotal = 0;
      limitedTopics.forEach((_, topicIndex) => {
        if (topicIndex < data.matrix.length && originalIdx >= 0 && originalIdx < data.matrix[topicIndex].length) {
          companyTotal += data.matrix[topicIndex][originalIdx] || 0;
        }
      });
      companyTotals.push(companyTotal);
    });

    // Create cells with both absolute and relative values
    let maxValue = 0;
    let maxRelativeValue = 0;
    const cells: HeatmapCell[] = [];

    limitedTopics.forEach((topic, topicIndex) => {
      const topicTotal = topicTotals[topicIndex];

      limitedCompanies.forEach((company, companyIndex) => {
        const originalCompanyIdx = getOriginalCompanyIndex(company);
        // Ensure we don't go out of bounds
        if (topicIndex < data.matrix.length && originalCompanyIdx >= 0 && originalCompanyIdx < data.matrix[topicIndex].length) {
          const value = data.matrix[topicIndex][originalCompanyIdx] || 0;
          const companyTotal = companyTotals[companyIndex];

          const relativeByTopic = topicTotal > 0 ? value / topicTotal : 0;
          const relativeByCompany = companyTotal > 0 ? value / companyTotal : 0;

          maxValue = Math.max(maxValue, value);
          maxRelativeValue = Math.max(maxRelativeValue, relativeByCompany); // Use company-based for max

          cells.push({
            topic,
            company,
            value,
            relativeByTopic,
            relativeByCompany,
            normalizedValue: normalizationMode === 'relative' ? relativeByCompany : 0, // Use company-based (Share of Company)
            x: companyIndex,
            y: topicIndex
          });
        }
      });
    });

    // Final normalization based on selected mode
    if (normalizationMode === 'absolute') {
      cells.forEach(cell => {
        cell.normalizedValue = maxValue > 0 ? cell.value / maxValue : 0;
      });
    } else {
      // Relative mode - use company-based normalization (Share of Company)
      cells.forEach(cell => {
        cell.normalizedValue = maxRelativeValue > 0 ? (cell.relativeByCompany || 0) / maxRelativeValue : 0;
      });
    }

    return { 
      cells, 
      maxValue, 
      maxRelativeValue,
      topics: limitedTopics, 
      companies: limitedCompanies,
      topicTotals
    };
  }, [data, maxTopics, maxCompanies, normalizationMode]);

  // Calculate cell dimensions
  const cellWidth = Math.max(60, Math.min(120, (800 - 200) / processedData.companies.length));
  const cellHeight = Math.max(25, Math.min(40, (height - 100) / processedData.topics.length));
  
  // Enhanced color schemes for better visibility
  const getColorScheme = (scheme: 'viridis' | 'plasma' | 'blues' | 'reds' | 'oranges' = 'viridis') => {
    switch (scheme) {
      case 'viridis':
        return ['#440154', '#482777', '#3f4a8a', '#31678e', '#26838f', '#1f9d8a', '#6cce5a', '#b6de2b', '#fee825'];
      case 'plasma':
        return ['#0d0887', '#5302a3', '#8b0aa5', '#b83289', '#db5c68', '#f48849', '#febd2a', '#f0f921'];
      case 'blues':
        return ['#f7fbff', '#deebf7', '#c6dbef', '#9ecae1', '#6baed6', '#4292c6', '#2171b5', '#08519c', '#08306b'];
      case 'reds':
        return ['#fff5f0', '#fee0d2', '#fcbba1', '#fc9272', '#fb6a4a', '#ef3b2c', '#cb181d', '#a50f15', '#67000d'];
      case 'oranges':
        return ['#fff5eb', '#fee6ce', '#fdd0a2', '#fdae6b', '#fd8d3c', '#f16913', '#d94801', '#a63603', '#7f2704'];
      default:
        return ['#440154', '#482777', '#3f4a8a', '#31678e', '#26838f', '#1f9d8a', '#6cce5a', '#b6de2b', '#fee825'];
    }
  };

  // Get color based on normalized value with better contrast
  const getCellColor = (normalizedValue: number, colorScheme: 'viridis' | 'plasma' | 'blues' | 'reds' | 'oranges' = 'plasma') => {
    if (normalizedValue === 0) return theme.palette.grey[50];
    
    const colors = getColorScheme(colorScheme);
    const intensity = Math.max(0.05, normalizedValue);
    
    // Map intensity to color index with better distribution
    let colorIndex;
    if (intensity < 0.1) {
      colorIndex = 0;
    } else if (intensity < 0.2) {
      colorIndex = 1;
    } else if (intensity < 0.35) {
      colorIndex = 2;
    } else if (intensity < 0.5) {
      colorIndex = 3;
    } else if (intensity < 0.65) {
      colorIndex = 4;
    } else if (intensity < 0.8) {
      colorIndex = 5;
    } else if (intensity < 0.9) {
      colorIndex = 6;
    } else if (intensity < 0.95) {
      colorIndex = 7;
    } else {
      colorIndex = 8;
    }
    
    return colors[Math.min(colorIndex, colors.length - 1)];
  };

  // Enhanced tooltip component with relative frequency
  const HeatmapTooltip = ({ cell }: { cell: HeatmapCell }) => {
    const topicTotal = processedData.topicTotals?.[processedData.topics.indexOf(cell.topic)] || 0;
    
    return (
      <Paper
        elevation={3}
        sx={{
          p: 1.5,
          maxWidth: 250,
          backgroundColor: 'background.paper',
          border: 1,
          borderColor: 'divider'
        }}
      >
        <Typography variant="body2" sx={{ fontWeight: 'bold', mb: 0.5 }}>
          {cell.topic}
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 0.5 }}>
          Company: {cell.company}
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Absolute Frequency: {cell.value.toLocaleString()}
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Topic Total: {topicTotal.toLocaleString()}
        </Typography>
        {/* Highlight the Share of Company since it drives the color */}
        <Box sx={{ 
          mt: 1, 
          p: 1, 
          backgroundColor: 'primary.light', 
          borderRadius: 1,
          border: 2,
          borderColor: 'primary.main'
        }}>
          <Typography variant="body2" sx={{ fontWeight: 'bold', color: 'primary.contrastText', textAlign: 'center' }}>
            🎨 Share of Company: {((cell.relativeByCompany || 0) * 100).toFixed(1)}%
          </Typography>
          <Typography variant="caption" sx={{ color: 'primary.contrastText', textAlign: 'center', display: 'block' }}>
            (This percentage determines the color)
          </Typography>
        </Box>
        <Typography variant="body2" sx={{ fontWeight: 500, color: 'text.secondary', mt: 0.5 }}>
          Share of Topic: {((cell.relativeByTopic || 0) * 100).toFixed(1)}%
        </Typography>
        <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5, display: 'block' }}>
          🎨 Color based on Share of Company (what % this topic is within the company)
        </Typography>
      </Paper>
    );
  };

  if (!data || processedData.cells.length === 0) {
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
          No heatmap data available
        </Typography>
      </Box>
    );
  }

  const chartWidth = 200 + (processedData.companies.length * cellWidth);
  const chartHeight = 60 + (processedData.topics.length * cellHeight);

  return (
    <Box sx={{ width: '100%', height, overflow: 'auto' }}>
      <Box sx={{ minWidth: chartWidth, minHeight: chartHeight, position: 'relative' }}>
        {/* Company labels (header) */}
        <Box sx={{ 
          position: 'absolute', 
          top: 0, 
          left: 200, 
          display: 'flex',
          height: 60
        }}>
          {processedData.companies.map((company) => (
            <Box
              key={company}
              sx={{
                width: cellWidth,
                height: 60,
                display: 'flex',
                alignItems: 'flex-end',
                justifyContent: 'center',
                pb: 1
              }}
            >
              <Typography
                variant="caption"
                sx={{
                  transform: 'rotate(-45deg)',
                  transformOrigin: 'center',
                  fontSize: '0.75rem',
                  fontWeight: 500,
                  whiteSpace: 'nowrap',
                  maxWidth: cellWidth * 1.5,
                  overflow: 'hidden',
                  textOverflow: 'ellipsis'
                }}
              >
                {company.length > 12 ? `${company.substring(0, 12)}...` : company}
              </Typography>
            </Box>
          ))}
        </Box>

        {/* Topic labels (left side) */}
        <Box sx={{ 
          position: 'absolute', 
          top: 60, 
          left: 0, 
          width: 200 
        }}>
          {processedData.topics.map((topic, index) => (
            <Box
              key={topic}
              sx={{
                width: 200,
                height: cellHeight,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'flex-end',
                pr: 1,
                borderBottom: index < processedData.topics.length - 1 ? 1 : 0,
                borderColor: 'divider'
              }}
            >
              <Typography
                variant="body2"
                sx={{
                  fontSize: '0.8rem',
                  fontWeight: 500,
                  textAlign: 'right',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  whiteSpace: 'nowrap'
                }}
              >
                {topic}
              </Typography>
            </Box>
          ))}
        </Box>

        {/* Heatmap cells */}
        <Box sx={{ 
          position: 'absolute', 
          top: 60, 
          left: 200 
        }}>
          {processedData.cells.map((cell, index) => (
            <Tooltip
              key={`${cell.topic}-${cell.company}-${index}`}
              title={<HeatmapTooltip cell={cell} />}
              placement="top"
              arrow
            >
              <Box
                sx={{
                  position: 'absolute',
                  left: cell.x * cellWidth,
                  top: cell.y * cellHeight,
                  width: cellWidth,
                  height: cellHeight,
                  backgroundColor: getCellColor(cell.normalizedValue, colorScheme),
                  border: cell.normalizedValue === 0 ? 1 : 2,
                  borderColor: cell.normalizedValue === 0 ? theme.palette.divider : 'rgba(255,255,255,0.3)',
                  cursor: 'pointer',
                  transition: 'all 0.2s ease',
                  boxShadow: cell.normalizedValue > 0.7 ? '0 0 8px rgba(0,0,0,0.3)' : 'none',
                  '&:hover': {
                    transform: 'scale(1.1)',
                    zIndex: 10,
                    boxShadow: '0 4px 12px rgba(0,0,0,0.4)',
                    border: 2,
                    borderColor: theme.palette.primary.main
                  }
                }}
              />
            </Tooltip>
          ))}
        </Box>

        {/* Enhanced Legend */}
        <Box sx={{ 
          position: 'absolute', 
          bottom: 10, 
          right: 20,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'flex-end',
          gap: 1,
          backgroundColor: 'background.paper',
          p: 2,
          borderRadius: 1,
          boxShadow: 1,
          border: 1,
          borderColor: 'divider'
        }}>
          <Typography variant="caption" sx={{ fontWeight: 'bold', mb: 1 }}>
            {normalizationMode === 'relative' ? 'Share of Company Scale' : 'Absolute Frequency Scale'}
          </Typography>
          <Typography variant="caption" color="text.secondary" sx={{ mb: 1, display: 'block' }}>
            {normalizationMode === 'relative' 
              ? '% of company\'s total questions by topic' 
              : 'Raw frequency values'
            }
          </Typography>
          <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 1 }}>
            {/* Color swatches */}
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Typography variant="caption" color="text.secondary" sx={{ minWidth: 30, fontSize: '0.7rem' }}>
                Low
              </Typography>
              <Box sx={{ display: 'flex', gap: 0.5 }}>
                {[0.05, 0.2, 0.35, 0.5, 0.65, 0.8, 0.95].map((intensity) => (
                  <Box
                    key={intensity}
                    sx={{
                      width: 24,
                      height: 24,
                      backgroundColor: getCellColor(intensity, colorScheme),
                      border: 1,
                      borderColor: 'divider',
                      borderRadius: 0.5,
                      position: 'relative'
                    }}
                    title={`${Math.round(intensity * (normalizationMode === 'relative' ? processedData.maxRelativeValue * 100 : processedData.maxValue))}${normalizationMode === 'relative' ? '%' : ''}`}
                  />
                ))}
              </Box>
              <Typography variant="caption" color="text.secondary" sx={{ minWidth: 30, fontSize: '0.7rem' }}>
                High
              </Typography>
            </Box>
            
            {/* Percentage labels */}
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Box sx={{ minWidth: 30 }} /> {/* Spacer for "Low" label */}
              <Box sx={{ display: 'flex', gap: 0.5 }}>
                {[0.05, 0.2, 0.35, 0.5, 0.65, 0.8, 0.95].map((intensity) => {
                  const actualValue = normalizationMode === 'relative' 
                    ? intensity * processedData.maxRelativeValue * 100
                    : intensity * processedData.maxValue;
                  const displayValue = normalizationMode === 'relative' 
                    ? `${actualValue.toFixed(0)}%`
                    : actualValue.toLocaleString();
                  
                  return (
                    <Typography
                      key={intensity}
                      variant="caption"
                      sx={{
                        width: 24,
                        textAlign: 'center',
                        fontSize: '0.65rem',
                        fontWeight: 500,
                        color: 'text.secondary'
                      }}
                    >
                      {displayValue}
                    </Typography>
                  );
                })}
              </Box>
              <Box sx={{ minWidth: 30 }} /> {/* Spacer for "High" label */}
            </Box>
          </Box>
          {/* Min/Max values with better formatting */}
          <Box sx={{ display: 'flex', justifyContent: 'space-between', width: '100%', mt: 1, pt: 1, borderTop: 1, borderColor: 'divider' }}>
            <Box sx={{ textAlign: 'left' }}>
              <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 'bold', fontSize: '0.7rem' }}>
                Min: {normalizationMode === 'relative' ? '0%' : '0'}
              </Typography>
            </Box>
            <Box sx={{ textAlign: 'right' }}>
              <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 'bold', fontSize: '0.7rem' }}>
                Max: {normalizationMode === 'relative' 
                  ? `${((processedData.maxRelativeValue || 0) * 100).toFixed(1)}%`
                  : processedData.maxValue.toLocaleString()
                }
              </Typography>
            </Box>
          </Box>
          
          {/* Helpful context */}
          <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5, fontStyle: 'italic', textAlign: 'center', fontSize: '0.65rem' }}>
            {normalizationMode === 'relative' 
              ? '💡 Higher % = More important for that company'
              : '📊 Raw frequency counts'
            }
          </Typography>
        </Box>
      </Box>
    </Box>
  );
}

// Normalization mode selector component
interface NormalizationModeSelectorProps {
  value: 'absolute' | 'relative';
  onChange: (mode: 'absolute' | 'relative') => void;
  size?: 'small' | 'medium';
}

export function NormalizationModeSelector({ 
  value, 
  onChange, 
  size = 'small' 
}: NormalizationModeSelectorProps) {
  const modes = [
    { 
      value: 'relative', 
      label: 'Share of Company (%)', 
      description: 'What % each topic is within company' 
    },
    { 
      value: 'absolute', 
      label: 'Absolute', 
      description: 'Raw frequency values' 
    }
  ] as const;

  return (
    <FormControl size={size} sx={{ minWidth: 140 }}>
      <InputLabel>Normalization</InputLabel>
      <Select
        value={value}
        label="Normalization"
        onChange={(e) => onChange(e.target.value as any)}
      >
        {modes.map((mode) => (
          <MenuItem key={mode.value} value={mode.value}>
            <Box>
              <Typography variant="body2">{mode.label}</Typography>
              <Typography variant="caption" color="text.secondary">
                {mode.description}
              </Typography>
            </Box>
          </MenuItem>
        ))}
      </Select>
    </FormControl>
  );
}

// Color scheme selector component
interface ColorSchemeSelectorProps {
  value: 'viridis' | 'plasma' | 'blues' | 'reds' | 'oranges';
  onChange: (scheme: 'viridis' | 'plasma' | 'blues' | 'reds' | 'oranges') => void;
  size?: 'small' | 'medium';
}

export function ColorSchemeSelector({ 
  value, 
  onChange, 
  size = 'small' 
}: ColorSchemeSelectorProps) {
  const colorSchemes = [
    { value: 'plasma', label: 'Plasma (Purple-Pink)', description: 'High contrast (Default)' },
    { value: 'viridis', label: 'Viridis (Purple-Green)', description: 'Colorblind-friendly' },
    { value: 'blues', label: 'Blues', description: 'Cool tones' },
    { value: 'reds', label: 'Reds', description: 'Warm tones' },
    { value: 'oranges', label: 'Oranges', description: 'Vibrant warm' }
  ] as const;

  return (
    <FormControl size={size} sx={{ minWidth: 160 }}>
      <InputLabel>Color Scheme</InputLabel>
      <Select
        value={value}
        label="Color Scheme"
        onChange={(e) => onChange(e.target.value as any)}
      >
        {colorSchemes.map((scheme) => (
          <MenuItem key={scheme.value} value={scheme.value}>
            <Box>
              <Typography variant="body2">{scheme.label}</Typography>
              <Typography variant="caption" color="text.secondary">
                {scheme.description}
              </Typography>
            </Box>
          </MenuItem>
        ))}
      </Select>
    </FormControl>
  );
}
