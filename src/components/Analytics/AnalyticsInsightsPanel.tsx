import React, { useState } from 'react';
import {
  Card,
  CardContent,
  Typography,
  Box,
  Chip,
  Alert,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  LinearProgress,
  Tooltip,
  Badge,
  Tabs,
  Tab
} from '@mui/material';
import {
  ExpandMore,
  TrendingUp,
  Pattern,
  Lightbulb,
  Warning,
  CheckCircle,
  Info
} from '@mui/icons-material';
import type { AnalyticsInsightsResponse, AnalyticsInsight } from '../../types/analytics';

interface AnalyticsInsightsPanelProps {
  insights: AnalyticsInsightsResponse;
}

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`insights-tabpanel-${index}`}
      aria-labelledby={`insights-tab-${index}`}
      {...other}
    >
      {value === index && <Box>{children}</Box>}
    </div>
  );
}

export const AnalyticsInsightsPanel: React.FC<AnalyticsInsightsPanelProps> = ({ insights }) => {
  const [activeTab, setActiveTab] = useState(0);
  const [expandedInsight, setExpandedInsight] = useState<string | false>(false);

  const handleTabChange = (_event: React.SyntheticEvent, newValue: number) => {
    setActiveTab(newValue);
  };

  const handleAccordionChange = (panel: string) => (_event: React.SyntheticEvent, isExpanded: boolean) => {
    setExpandedInsight(isExpanded ? panel : false);
  };

  const getInsightIcon = (type: AnalyticsInsight['type']) => {
    switch (type) {
      case 'trend':
        return <TrendingUp />;
      case 'pattern':
        return <Pattern />;
      case 'recommendation':
        return <Lightbulb />;
      case 'anomaly':
        return <Warning />;
      default:
        return <Info />;
    }
  };

  const getInsightColor = (type: AnalyticsInsight['type']) => {
    switch (type) {
      case 'trend':
        return 'primary';
      case 'pattern':
        return 'secondary';
      case 'recommendation':
        return 'success';
      case 'anomaly':
        return 'warning';
      default:
        return 'default';
    }
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return 'success';
    if (confidence >= 0.6) return 'warning';
    return 'error';
  };

  const filterInsightsByType = (type: string) => {
    return insights.insights.filter(insight => insight.type === type);
  };

  const renderInsightCard = (insight: AnalyticsInsight) => (
    <Accordion
      key={insight.id}
      expanded={expandedInsight === insight.id}
      onChange={handleAccordionChange(insight.id)}
      sx={{ mb: 1 }}
    >
      <AccordionSummary expandIcon={<ExpandMore />}>
        <Box display="flex" alignItems="center" width="100%">
          <Box sx={{ mr: 2 }}>
            {getInsightIcon(insight.type)}
          </Box>
          <Box flexGrow={1}>
            <Typography variant="subtitle1" sx={{ fontWeight: 'medium' }}>
              {insight.title}
            </Typography>
            <Box display="flex" alignItems="center" gap={1} mt={0.5}>
              <Chip
                label={insight.type}
                size="small"
                color={getInsightColor(insight.type) as any}
                variant="outlined"
              />
              <Chip
                label={`${(insight.confidence * 100).toFixed(0)}% confidence`}
                size="small"
                color={getConfidenceColor(insight.confidence) as any}
              />
              {insight.actionable && (
                <Tooltip title="Actionable insight">
                  <CheckCircle color="success" fontSize="small" />
                </Tooltip>
              )}
            </Box>
          </Box>
        </Box>
      </AccordionSummary>
      <AccordionDetails>
        <Box>
          <Typography variant="body2" paragraph>
            {insight.description}
          </Typography>

          {insight.recommendation && (
            <Alert severity="info" sx={{ mb: 2 }}>
              <Typography variant="body2">
                <strong>Recommendation:</strong> {insight.recommendation}
              </Typography>
            </Alert>
          )}

          {insight.companies && insight.companies.length > 0 && (
            <Box mb={2}>
              <Typography variant="caption" color="text.secondary" gutterBottom>
                Related Companies:
              </Typography>
              <Box display="flex" flexWrap="wrap" gap={0.5} mt={0.5}>
                {insight.companies.map((company) => (
                  <Chip key={company} label={company} size="small" variant="outlined" />
                ))}
              </Box>
            </Box>
          )}

          {insight.topics && insight.topics.length > 0 && (
            <Box mb={2}>
              <Typography variant="caption" color="text.secondary" gutterBottom>
                Related Topics:
              </Typography>
              <Box display="flex" flexWrap="wrap" gap={0.5} mt={0.5}>
                {insight.topics.map((topic) => (
                  <Chip key={topic} label={topic} size="small" variant="outlined" />
                ))}
              </Box>
            </Box>
          )}

          {insight.metrics && Object.keys(insight.metrics).length > 0 && (
            <Box>
              <Typography variant="caption" color="text.secondary" gutterBottom>
                Key Metrics:
              </Typography>
              <Box mt={1}>
                {Object.entries(insight.metrics).map(([metric, value]) => (
                  <Box key={metric} display="flex" justifyContent="space-between" alignItems="center" mb={0.5}>
                    <Typography variant="body2">{metric}:</Typography>
                    <Typography variant="body2" fontWeight="medium">
                      {typeof value === 'number' 
                        ? value.toFixed(2) 
                        : typeof value === 'object' && value !== null
                        ? JSON.stringify(value)
                        : String(value)
                      }
                    </Typography>
                  </Box>
                ))}
              </Box>
            </Box>
          )}

          <Box mt={2}>
            <LinearProgress
              variant="determinate"
              value={insight.confidence * 100}
              color={getConfidenceColor(insight.confidence) as any}
              sx={{ height: 6, borderRadius: 3 }}
            />
            <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5, display: 'block' }}>
              Confidence: {(insight.confidence * 100).toFixed(1)}%
            </Typography>
          </Box>
        </Box>
      </AccordionDetails>
    </Accordion>
  );

  const trendInsights = filterInsightsByType('trend');
  const patternInsights = filterInsightsByType('pattern');
  const recommendationInsights = filterInsightsByType('recommendation');
  const anomalyInsights = filterInsightsByType('anomaly');

  return (
    <Card>
      <CardContent>
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
          <Typography variant="h5">
            AI-Powered Insights
          </Typography>
          <Box display="flex" gap={1}>
            <Chip
              label={`${insights.totalInsights} insights`}
              color="primary"
              variant="outlined"
            />
            <Chip
              label={`${insights.confidence.high} high confidence`}
              color="success"
              variant="outlined"
            />
          </Box>
        </Box>

        {/* Confidence Summary */}
        <Box mb={3}>
          <Typography variant="body2" color="text.secondary" gutterBottom>
            Confidence Distribution
          </Typography>
          <Box display="flex" gap={2}>
            <Box display="flex" alignItems="center" gap={0.5}>
              <Box sx={{ width: 12, height: 12, bgcolor: 'success.main', borderRadius: '50%' }} />
              <Typography variant="caption">High ({insights.confidence.high})</Typography>
            </Box>
            <Box display="flex" alignItems="center" gap={0.5}>
              <Box sx={{ width: 12, height: 12, bgcolor: 'warning.main', borderRadius: '50%' }} />
              <Typography variant="caption">Medium ({insights.confidence.medium})</Typography>
            </Box>
            <Box display="flex" alignItems="center" gap={0.5}>
              <Box sx={{ width: 12, height: 12, bgcolor: 'error.main', borderRadius: '50%' }} />
              <Typography variant="caption">Low ({insights.confidence.low})</Typography>
            </Box>
          </Box>
        </Box>

        {/* Tabs for different insight types */}
        <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 2 }}>
          <Tabs value={activeTab} onChange={handleTabChange} variant="scrollable" scrollButtons="auto">
            <Tab
              icon={
                <Badge badgeContent={trendInsights.length} color="primary">
                  <TrendingUp />
                </Badge>
              }
              label="Trends"
            />
            <Tab
              icon={
                <Badge badgeContent={patternInsights.length} color="secondary">
                  <Pattern />
                </Badge>
              }
              label="Patterns"
            />
            <Tab
              icon={
                <Badge badgeContent={recommendationInsights.length} color="success">
                  <Lightbulb />
                </Badge>
              }
              label="Recommendations"
            />
            <Tab
              icon={
                <Badge badgeContent={anomalyInsights.length} color="warning">
                  <Warning />
                </Badge>
              }
              label="Anomalies"
            />
          </Tabs>
        </Box>

        {/* Tab Panels */}
        <TabPanel value={activeTab} index={0}>
          {trendInsights.length > 0 ? (
            trendInsights.map(renderInsightCard)
          ) : (
            <Typography variant="body2" color="text.secondary" textAlign="center" py={4}>
              No trend insights available
            </Typography>
          )}
        </TabPanel>

        <TabPanel value={activeTab} index={1}>
          {patternInsights.length > 0 ? (
            patternInsights.map(renderInsightCard)
          ) : (
            <Typography variant="body2" color="text.secondary" textAlign="center" py={4}>
              No pattern insights available
            </Typography>
          )}
        </TabPanel>

        <TabPanel value={activeTab} index={2}>
          {recommendationInsights.length > 0 ? (
            recommendationInsights.map(renderInsightCard)
          ) : (
            <Typography variant="body2" color="text.secondary" textAlign="center" py={4}>
              No recommendation insights available
            </Typography>
          )}
        </TabPanel>

        <TabPanel value={activeTab} index={3}>
          {anomalyInsights.length > 0 ? (
            anomalyInsights.map(renderInsightCard)
          ) : (
            <Typography variant="body2" color="text.secondary" textAlign="center" py={4}>
              No anomaly insights available
            </Typography>
          )}
        </TabPanel>
      </CardContent>
    </Card>
  );
};