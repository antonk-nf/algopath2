import { Box, Typography, Chip, Tooltip } from '@mui/material';
import { 
  TrendingUp, 
  TrendingDown, 
  TrendingFlat,
  ArrowUpward,
  ArrowDownward,
  Remove
} from '@mui/icons-material';
import { useTheme } from '@mui/material/styles';

interface TopicTrendIndicatorProps {
  trendDirection?: string;
  trendStrength?: number;
  size?: 'small' | 'medium' | 'large';
  showPercentage?: boolean;
  showLabel?: boolean;
  variant?: 'icon' | 'chip' | 'full';
}

export function TopicTrendIndicator({
  trendDirection,
  trendStrength,
  size = 'medium',
  showPercentage = true,
  showLabel = false,
  variant = 'full'
}: TopicTrendIndicatorProps) {
  const theme = useTheme();

  // Normalize trend direction
  const normalizedDirection = (trendDirection || '').toLowerCase();
  
  // Determine trend type
  const isIncreasing = ['increasing', 'up', 'rising', 'positive'].includes(normalizedDirection);
  const isDecreasing = ['decreasing', 'down', 'falling', 'negative'].includes(normalizedDirection);
  // const isStable = ['stable', 'flat', 'neutral'].includes(normalizedDirection) || (!isIncreasing && !isDecreasing);

  // Get appropriate colors
  const getColor = () => {
    if (isIncreasing) return theme.palette.success.main;
    if (isDecreasing) return theme.palette.error.main;
    return theme.palette.action.active;
  };

  // Get appropriate icon
  const getIcon = () => {
    const iconSize = size === 'small' ? 16 : size === 'large' ? 24 : 20;
    const iconProps = { sx: { fontSize: iconSize, color: getColor() } };

    if (variant === 'icon') {
      if (isIncreasing) return <ArrowUpward {...iconProps} />;
      if (isDecreasing) return <ArrowDownward {...iconProps} />;
      return <Remove {...iconProps} />;
    }

    if (isIncreasing) return <TrendingUp {...iconProps} />;
    if (isDecreasing) return <TrendingDown {...iconProps} />;
    return <TrendingFlat {...iconProps} />;
  };

  // Format percentage
  const formatPercentage = (strength?: number) => {
    if (strength === undefined || Number.isNaN(strength)) return '—';
    const percentage = Math.abs(strength * 100);
    return `${percentage.toFixed(1)}%`;
  };

  // Get trend label
  const getTrendLabel = () => {
    if (isIncreasing) return 'Increasing';
    if (isDecreasing) return 'Decreasing';
    return 'Stable';
  };

  // Get chip color
  const getChipColor = (): 'success' | 'error' | 'default' => {
    if (isIncreasing) return 'success';
    if (isDecreasing) return 'error';
    return 'default';
  };

  // Tooltip content
  const tooltipContent = (
    <Box>
      <Typography variant="body2" sx={{ fontWeight: 'bold' }}>
        Trend: {getTrendLabel()}
      </Typography>
      {trendStrength !== undefined && !Number.isNaN(trendStrength) && (
        <Typography variant="body2">
          Strength: {formatPercentage(trendStrength)}
        </Typography>
      )}
      <Typography variant="caption" color="text.secondary">
        Based on recent frequency changes
      </Typography>
    </Box>
  );

  // Render based on variant
  if (variant === 'icon') {
    return (
      <Tooltip title={tooltipContent} arrow>
        <Box sx={{ display: 'inline-flex', alignItems: 'center' }}>
          {getIcon()}
        </Box>
      </Tooltip>
    );
  }

  if (variant === 'chip') {
    return (
      <Tooltip title={tooltipContent} arrow>
        <Chip
          icon={getIcon()}
          label={showPercentage ? formatPercentage(trendStrength) : getTrendLabel()}
          color={getChipColor()}
          variant="outlined"
          size={size === 'large' ? 'medium' : 'small'}
        />
      </Tooltip>
    );
  }

  // Full variant (default)
  return (
    <Tooltip title={tooltipContent} arrow>
      <Box 
        sx={{ 
          display: 'inline-flex', 
          alignItems: 'center', 
          gap: 0.5,
          cursor: 'help'
        }}
      >
        {getIcon()}
        {showLabel && (
          <Typography 
            variant={size === 'small' ? 'caption' : 'body2'} 
            sx={{ color: getColor(), fontWeight: 500 }}
          >
            {getTrendLabel()}
          </Typography>
        )}
        {showPercentage && trendStrength !== undefined && !Number.isNaN(trendStrength) && (
          <Typography 
            variant={size === 'small' ? 'caption' : 'body2'} 
            sx={{ color: getColor() }}
          >
            {formatPercentage(trendStrength)}
          </Typography>
        )}
      </Box>
    </Tooltip>
  );
}

// Helper component for displaying multiple trend indicators in a list
interface TopicTrendListProps {
  trends: Array<{
    topic: string;
    trendDirection?: string;
    trendStrength?: number;
  }>;
  maxItems?: number;
}

export function TopicTrendList({ trends, maxItems = 10 }: TopicTrendListProps) {
  const displayTrends = trends.slice(0, maxItems);

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
      {displayTrends.map((trend, index) => (
        <Box 
          key={`${trend.topic}-${index}`}
          sx={{ 
            display: 'flex', 
            alignItems: 'center', 
            justifyContent: 'space-between',
            py: 0.5,
            px: 1,
            borderRadius: 1,
            '&:hover': {
              backgroundColor: 'action.hover'
            }
          }}
        >
          <Typography variant="body2" sx={{ flex: 1, mr: 2 }}>
            {trend.topic}
          </Typography>
          <TopicTrendIndicator
            trendDirection={trend.trendDirection}
            trendStrength={trend.trendStrength}
            size="small"
            variant="chip"
          />
        </Box>
      ))}
    </Box>
  );
}