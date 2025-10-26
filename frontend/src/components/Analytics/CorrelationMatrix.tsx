import React, { useState } from 'react';
import {
  Card,
  CardContent,
  Typography,
  Box,
  Chip,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  type SelectChangeEvent
} from '@mui/material';
import type { AnalyticsCorrelationResponse } from '../../types/analytics';

interface CorrelationMatrixProps {
  correlations: AnalyticsCorrelationResponse;
}

export const CorrelationMatrix: React.FC<CorrelationMatrixProps> = ({ correlations }) => {
  const [selectedMetric, setSelectedMetric] = useState<string>(correlations.metrics[0] || 'all');

  const handleMetricChange = (event: SelectChangeEvent) => {
    setSelectedMetric(event.target.value);
  };

  // Filter correlations by selected metric (currently all correlations are shown as metric property is not available)
  const filteredCorrelations = correlations.correlations;

  const getCorrelationColor = (correlation: number) => {
    const abs = Math.abs(correlation);
    if (abs >= 0.8) return '#4caf50'; // Strong - Green
    if (abs >= 0.5) return '#ff9800'; // Moderate - Orange  
    if (abs >= 0.3) return '#2196f3'; // Weak - Blue
    return '#9e9e9e'; // Very weak - Grey
  };



  return (
    <Card>
      <CardContent>
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
          <Typography variant="h5">
            Correlation Analysis
          </Typography>
          <Box display="flex" gap={2} alignItems="center">
            <FormControl size="small" sx={{ minWidth: 120 }}>
              <InputLabel>Metric</InputLabel>
              <Select
                value={selectedMetric}
                onChange={handleMetricChange}
                label="Metric"
              >
                <MenuItem value="all">All Metrics</MenuItem>
                {correlations.metrics.map((metric) => (
                  <MenuItem key={metric} value={metric}>
                    {metric}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
            <Chip
              label={`${filteredCorrelations.length} correlations`}
              color="primary"
              variant="outlined"
            />
          </Box>
        </Box>

        {/* Summary Statistics */}
        <Box sx={{ 
          display: 'grid', 
          gridTemplateColumns: { xs: '1fr', sm: 'repeat(4, 1fr)' }, 
          gap: 2, 
          mb: 3 
        }}>
          <Card variant="outlined">
            <CardContent sx={{ textAlign: 'center', py: 2 }}>
              <Typography variant="h6" color="success.main">
                {correlations.summary.strongCorrelations}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Strong Correlations
              </Typography>
            </CardContent>
          </Card>
          
          <Card variant="outlined">
            <CardContent sx={{ textAlign: 'center', py: 2 }}>
              <Typography variant="h6" color="primary.main">
                {correlations.summary.totalPairs}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Total Pairs
              </Typography>
            </CardContent>
          </Card>
          
          <Card variant="outlined">
            <CardContent sx={{ textAlign: 'center', py: 2 }}>
              <Typography variant="h6" color="text.primary">
                {correlations.summary.avgCorrelation.toFixed(3)}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Avg Correlation
              </Typography>
            </CardContent>
          </Card>
          
          <Card variant="outlined">
            <CardContent sx={{ textAlign: 'center', py: 2 }}>
              <Typography variant="h6" color="secondary.main">
                {correlations.companies.length}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Companies
              </Typography>
            </CardContent>
          </Card>
        </Box>

        {/* Correlation Legend */}
        <Box mb={3}>
          <Typography variant="body2" color="text.secondary" gutterBottom>
            Correlation Strength:
          </Typography>
          <Box display="flex" gap={2} flexWrap="wrap">
            <Chip label="Strong (≥0.8)" sx={{ bgcolor: '#4caf5020', color: '#4caf50' }} size="small" />
            <Chip label="Moderate (0.5-0.8)" sx={{ bgcolor: '#ff980020', color: '#ff9800' }} size="small" />
            <Chip label="Weak (0.3-0.5)" sx={{ bgcolor: '#2196f320', color: '#2196f3' }} size="small" />
            <Chip label="Very Weak (<0.3)" sx={{ bgcolor: '#9e9e9e20', color: '#9e9e9e' }} size="small" />
          </Box>
        </Box>

        {/* Top Correlations */}
        <Box>
          <Typography variant="h6" gutterBottom>
            Strongest Correlations
          </Typography>
          {filteredCorrelations
            .sort((a, b) => Math.abs(b.correlation) - Math.abs(a.correlation))
            .slice(0, 10)
            .map((corr, index) => (
              <Box key={index} display="flex" justifyContent="space-between" alignItems="center" mb={1}>
                <Typography variant="body2">
                  {corr.company1} ↔ {corr.company2}
                </Typography>
                <Chip
                  label={corr.correlation.toFixed(3)}
                  size="small"
                  sx={{ 
                    bgcolor: `${getCorrelationColor(corr.correlation)}20`,
                    color: getCorrelationColor(corr.correlation)
                  }}
                />
              </Box>
            ))}
        </Box>
      </CardContent>
    </Card>
  );
};