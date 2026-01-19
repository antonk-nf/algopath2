import { useState } from 'react';
import {
  Box,
  Typography,
  Chip,
  Card,
  CardContent,
  Button,
  Collapse,
  Divider
} from '@mui/material';
import {
  Info as InfoIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
  Build as BuildIcon,
  Speed as SpeedIcon,
  Security as SecurityIcon
} from '@mui/icons-material';
import { config, getConfigSummary, isDevelopment } from '../../config/environment';

interface AppInfoProps {
  compact?: boolean;
}

export function AppInfo({ compact = false }: AppInfoProps) {
  const [expanded, setExpanded] = useState(false);
  const configSummary = getConfigSummary();

  const getEnvironmentColor = () => {
    switch (config.appEnv) {
      case 'production': return 'success';
      case 'staging': return 'warning';
      case 'development': return 'info';
      default: return 'default';
    }
  };

  if (compact) {
    return (
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <Chip
          label={`v${config.version}`}
          size="small"
          color="primary"
          variant="outlined"
        />
        <Chip
          label={config.appEnv}
          size="small"
          color={getEnvironmentColor()}
          variant="outlined"
        />
      </Box>
    );
  }

  return (
    <Card>
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
          <InfoIcon color="primary" />
          <Typography variant="h6">
            Application Information
          </Typography>
          <Button
            size="small"
            onClick={() => setExpanded(!expanded)}
            endIcon={expanded ? <ExpandLessIcon /> : <ExpandMoreIcon />}
          >
            {expanded ? 'Less' : 'More'}
          </Button>
        </Box>

        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2, mb: 2 }}>
          <Box sx={{ flex: '1 1 200px', textAlign: 'center', minWidth: 150 }}>
            <BuildIcon sx={{ fontSize: 32, color: 'primary.main', mb: 1 }} />
            <Typography variant="subtitle2">Version</Typography>
            <Typography variant="h6">{config.version}</Typography>
          </Box>
          
          <Box sx={{ flex: '1 1 200px', textAlign: 'center', minWidth: 150 }}>
            <SecurityIcon sx={{ fontSize: 32, color: 'success.main', mb: 1 }} />
            <Typography variant="subtitle2">Environment</Typography>
            <Chip
              label={config.appEnv}
              color={getEnvironmentColor()}
              size="small"
            />
          </Box>
          
          <Box sx={{ flex: '1 1 200px', textAlign: 'center', minWidth: 150 }}>
            <SpeedIcon sx={{ fontSize: 32, color: 'warning.main', mb: 1 }} />
            <Typography variant="subtitle2">API Timeout</Typography>
            <Typography variant="body2">{config.apiTimeout / 1000}s</Typography>
          </Box>
          
          <Box sx={{ flex: '1 1 200px', textAlign: 'center', minWidth: 150 }}>
            <InfoIcon sx={{ fontSize: 32, color: 'info.main', mb: 1 }} />
            <Typography variant="subtitle2">Build Time</Typography>
            <Typography variant="body2">
              {new Date(config.buildTime).toLocaleDateString()}
            </Typography>
          </Box>
        </Box>

        <Collapse in={expanded}>
          <Divider sx={{ mb: 2 }} />
          
          <Typography variant="subtitle1" gutterBottom>
            Configuration Details
          </Typography>
          
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 3 }}>
            <Box sx={{ flex: '1 1 300px', minWidth: 250 }}>
              <Typography variant="subtitle2" gutterBottom>
                API Configuration
              </Typography>
              <Box sx={{ pl: 2 }}>
                <Typography variant="body2">
                  <strong>URL:</strong> {config.apiUrl}
                </Typography>
                <Typography variant="body2">
                  <strong>Timeout:</strong> {config.apiTimeout}ms
                </Typography>
              </Box>
            </Box>
            
            <Box sx={{ flex: '1 1 300px', minWidth: 250 }}>
              <Typography variant="subtitle2" gutterBottom>
                Feature Flags
              </Typography>
              <Box sx={{ pl: 2, display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                <Chip
                  label="Analytics"
                  size="small"
                  color={config.enableAnalytics ? 'success' : 'default'}
                  variant="outlined"
                />
                <Chip
                  label="Onboarding"
                  size="small"
                  color={config.enableOnboarding ? 'success' : 'default'}
                  variant="outlined"
                />
                <Chip
                  label="Error Reporting"
                  size="small"
                  color={config.enableErrorReporting ? 'success' : 'default'}
                  variant="outlined"
                />
                <Chip
                  label="Service Worker"
                  size="small"
                  color={config.enableServiceWorker ? 'success' : 'default'}
                  variant="outlined"
                />
              </Box>
            </Box>
            
            <Box sx={{ flex: '1 1 300px', minWidth: 250 }}>
              <Typography variant="subtitle2" gutterBottom>
                Cache Configuration
              </Typography>
              <Box sx={{ pl: 2 }}>
                <Typography variant="body2">
                  <strong>Duration:</strong> {Math.round(config.cacheDuration / 1000 / 60)} minutes
                </Typography>
                <Typography variant="body2">
                  <strong>Max Size:</strong> {Math.round(config.maxCacheSize / 1024 / 1024)} MB
                </Typography>
              </Box>
            </Box>
            
            <Box sx={{ flex: '1 1 300px', minWidth: 250 }}>
              <Typography variant="subtitle2" gutterBottom>
                Debug Configuration
              </Typography>
              <Box sx={{ pl: 2 }}>
                <Typography variant="body2">
                  <strong>Debug Mode:</strong> {config.debugMode ? 'Enabled' : 'Disabled'}
                </Typography>
                <Typography variant="body2">
                  <strong>Log Level:</strong> {config.logLevel}
                </Typography>
              </Box>
            </Box>
          </Box>

          {isDevelopment && (
            <Box sx={{ mt: 2, p: 2, backgroundColor: 'info.50', borderRadius: 1 }}>
              <Typography variant="caption" component="pre" sx={{ fontSize: '0.75rem' }}>
                {JSON.stringify(configSummary, null, 2)}
              </Typography>
            </Box>
          )}
        </Collapse>
      </CardContent>
    </Card>
  );
}