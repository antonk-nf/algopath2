
import { Box, Tooltip, IconButton } from '@mui/material';
import { 
  Circle as CircleIcon,
  Refresh as RefreshIcon 
} from '@mui/icons-material';
import { useApiHealth } from '../../hooks/useAppState';
import { useHealthCheck } from '../../hooks/useApi';

export function HealthIndicator() {
  const apiHealth = useApiHealth();
  const { loading, refetch } = useHealthCheck();

  const getStatusColor = () => {
    switch (apiHealth.status) {
      case 'healthy':
        return '#4caf50'; // Green
      case 'degraded':
        return '#ff9800'; // Orange/Yellow
      case 'unhealthy':
        return '#f44336'; // Red
      default:
        return '#9e9e9e'; // Gray
    }
  };

  const getStatusText = () => {
    switch (apiHealth.status) {
      case 'healthy':
        return 'API is healthy';
      case 'degraded':
        return 'API is experiencing issues';
      case 'unhealthy':
        return 'API is unavailable';
      default:
        return 'API status unknown';
    }
  };

  const formatLastCheck = () => {
    try {
      const date = new Date(apiHealth.lastCheck);
      return `Last checked: ${date.toLocaleTimeString()}`;
    } catch {
      return 'Last check: Unknown';
    }
  };

  return (
    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
      <Tooltip 
        title={
          <Box>
            <div>{getStatusText()}</div>
            <div>{formatLastCheck()}</div>
          </Box>
        }
        arrow
      >
        <CircleIcon 
          sx={{ 
            color: getStatusColor(),
            fontSize: 16,
            filter: loading ? 'opacity(0.5)' : 'none'
          }} 
        />
      </Tooltip>
      
      <Tooltip title="Refresh API status">
        <IconButton
          size="small"
          onClick={refetch}
          disabled={loading}
          sx={{ 
            color: 'inherit',
            '&:hover': {
              backgroundColor: 'rgba(255, 255, 255, 0.1)'
            }
          }}
        >
          <RefreshIcon 
            sx={{ 
              fontSize: 18,
              animation: loading ? 'spin 1s linear infinite' : 'none',
              '@keyframes spin': {
                '0%': { transform: 'rotate(0deg)' },
                '100%': { transform: 'rotate(360deg)' }
              }
            }} 
          />
        </IconButton>
      </Tooltip>
    </Box>
  );
}