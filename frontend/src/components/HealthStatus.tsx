
import { 
  Card, 
  CardContent, 
  Typography, 
  Box, 
  Chip, 
  Button,
  CircularProgress 
} from '@mui/material';
import { 
  CheckCircle as CheckCircleIcon, 
  Warning as WarningIcon, 
  Error as ErrorIcon,
  Refresh as RefreshIcon 
} from '@mui/icons-material';
import { useHealthCheck } from '../hooks/useApi';
import { useApiHealth } from '../hooks/useAppState';

export function HealthStatus() {
  const { data, loading, error, refetch } = useHealthCheck();
  const apiHealth = useApiHealth();

  const getStatusIcon = () => {
    if (loading) return <CircularProgress size={20} />;
    
    switch (apiHealth.status) {
      case 'healthy':
        return <CheckCircleIcon color="success" />;
      case 'degraded':
        return <WarningIcon color="warning" />;
      case 'unhealthy':
        return <ErrorIcon color="error" />;
      default:
        return <ErrorIcon color="error" />;
    }
  };

  const getStatusColor = () => {
    switch (apiHealth.status) {
      case 'healthy':
        return 'success';
      case 'degraded':
        return 'warning';
      case 'unhealthy':
        return 'error';
      default:
        return 'error';
    }
  };

  const formatTimestamp = (timestamp: string) => {
    try {
      return new Date(timestamp).toLocaleString();
    } catch {
      return 'Unknown';
    }
  };

  return (
    <Card>
      <CardContent>
        <Box display="flex" alignItems="center" justifyContent="space-between" mb={2}>
          <Typography variant="h6" component="h2">
            API Health Status
          </Typography>
          <Button
            startIcon={<RefreshIcon />}
            onClick={refetch}
            disabled={loading}
            size="small"
          >
            Refresh
          </Button>
        </Box>

        <Box display="flex" alignItems="center" gap={2} mb={2}>
          {getStatusIcon()}
          <Chip 
            label={apiHealth.status.toUpperCase()} 
            color={getStatusColor() as 'success' | 'warning' | 'error'}
            variant="outlined"
          />
        </Box>

        {data && (
          <Box>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              Version: {data.version}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Last Check: {formatTimestamp(apiHealth.lastCheck)}
            </Typography>
          </Box>
        )}

        {error && (
          <Box mt={2}>
            <Typography variant="body2" color="error">
              Error: {error}
            </Typography>
          </Box>
        )}

        <Box mt={2}>
          <Typography variant="body2" color="text.secondary" gutterBottom>
            Endpoint Status:
          </Typography>
          {Object.entries(apiHealth.endpointStatus).map(([endpoint, status]) => (
            <Box key={endpoint} display="flex" alignItems="center" gap={1}>
              <Typography variant="body2">{endpoint}:</Typography>
              <Chip 
                label={status} 
                size="small"
                color={status === 'working' ? 'success' : status === 'slow' ? 'warning' : 'error'}
                variant="outlined"
              />
            </Box>
          ))}
        </Box>
      </CardContent>
    </Card>
  );
}