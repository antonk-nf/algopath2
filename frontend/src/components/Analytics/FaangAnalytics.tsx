import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  CircularProgress,
  Alert,
  Chip,
  Tabs,
  Tab,
  Button
} from '@mui/material';
import {
  TrendingUp,
  Compare,
  Insights,
  Star,
  Refresh
} from '@mui/icons-material';
import { analyticsService } from '../../services/analyticsService';
import { AnalyticsSummaryCard } from './AnalyticsSummaryCard';
import { AnalyticsInsightsPanel } from './AnalyticsInsightsPanel';
import { CompanyComparisonChart } from './CompanyComparisonChart';
import { CorrelationMatrix } from './CorrelationMatrix';
import type {
  AnalyticsSummary,
  AnalyticsInsightsResponse,
  CompanyComparison,
  AnalyticsCorrelationResponse
} from '../../types/analytics';
import { FAANG_COMPANIES } from '../../types/analytics';

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
      id={`faang-tabpanel-${index}`}
      aria-labelledby={`faang-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ py: 2 }}>{children}</Box>}
    </div>
  );
}

export const FaangAnalytics: React.FC = () => {
  const [activeTab, setActiveTab] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // FAANG analytics data
  const [summary, setSummary] = useState<AnalyticsSummary | null>(null);
  const [insights, setInsights] = useState<AnalyticsInsightsResponse | null>(null);
  const [comparison, setComparison] = useState<CompanyComparison | null>(null);
  const [correlations, setCorrelations] = useState<AnalyticsCorrelationResponse | null>(null);

  const handleTabChange = (_event: React.SyntheticEvent, newValue: number) => {
    setActiveTab(newValue);
  };

  const loadFaangAnalytics = async () => {
    try {
      setLoading(true);
      setError(null);

      const faangData = await analyticsService.getFaangAnalytics();
      
      setSummary(faangData.summary);
      setInsights(faangData.insights);
      setComparison(faangData.comparison);
      setCorrelations(faangData.correlations || null);
    } catch (err) {
      console.error('Failed to load FAANG analytics:', err);
      setError('Failed to load FAANG analytics. Some companies may not be available in the dataset.');
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = () => {
    analyticsService.clearCache();
    loadFaangAnalytics();
  };

  useEffect(() => {
    loadFaangAnalytics();
  }, []);

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress size={60} />
      </Box>
    );
  }

  return (
    <Box>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Box>
          <Typography variant="h5" gutterBottom>
            <Star sx={{ mr: 1, verticalAlign: 'middle', color: 'gold' }} />
            FAANG Companies Analysis
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Specialized analytics for major tech companies: Meta, Amazon, Google, and Microsoft
          </Typography>
        </Box>
        <Button
          variant="outlined"
          startIcon={<Refresh />}
          onClick={handleRefresh}
          disabled={loading}
          size="small"
        >
          Refresh
        </Button>
      </Box>

      {error && (
        <Alert severity="warning" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {/* Major Tech Company Chips */}
      <Box display="flex" flexWrap="wrap" gap={1} mb={3}>
        {FAANG_COMPANIES.map((company, index) => {
          const colors = ['#4285f4', '#ff9900', '#1877f2', '#00a1f1']; // Google, Amazon, Meta, Microsoft
          return (
            <Chip
              key={company}
              label={company}
              sx={{
                bgcolor: colors[index],
                color: 'white',
                fontWeight: 'medium',
                '&:hover': {
                  bgcolor: colors[index],
                  opacity: 0.8
                }
              }}
            />
          );
        })}
      </Box>

      {/* Quick Stats */}
      {summary && (
        <Box sx={{ 
          display: 'grid', 
          gridTemplateColumns: { xs: 'repeat(2, 1fr)', sm: 'repeat(4, 1fr)' }, 
          gap: 2, 
          mb: 3 
        }}>
          <Card variant="outlined">
            <CardContent sx={{ textAlign: 'center', py: 2 }}>
              <Typography variant="h6" color="primary.main">
                {summary.totalProblems.toLocaleString()}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Total Problems
              </Typography>
            </CardContent>
          </Card>
          
          <Card variant="outlined">
            <CardContent sx={{ textAlign: 'center', py: 2 }}>
              <Typography variant="h6" color="secondary.main">
                {summary.avgProblemsPerCompany.toFixed(0)}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Avg per Company
              </Typography>
            </CardContent>
          </Card>
          
          <Card variant="outlined">
            <CardContent sx={{ textAlign: 'center', py: 2 }}>
              <Typography variant="h6" color="success.main">
                {summary.topTopics.length}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Popular Topics
              </Typography>
            </CardContent>
          </Card>
          
          <Card variant="outlined">
            <CardContent sx={{ textAlign: 'center', py: 2 }}>
              <Typography variant="h6" color="warning.main">
                {insights?.confidence.high || 0}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                High Confidence Insights
              </Typography>
            </CardContent>
          </Card>
        </Box>
      )}

      {/* Tabs */}
      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 2 }}>
        <Tabs value={activeTab} onChange={handleTabChange} variant="scrollable" scrollButtons="auto">
          <Tab 
            icon={<TrendingUp />} 
            label="Overview" 
            id="faang-tab-0"
            aria-controls="faang-tabpanel-0"
          />
          <Tab 
            icon={<Compare />} 
            label="Comparison" 
            id="faang-tab-1"
            aria-controls="faang-tabpanel-1"
          />
          <Tab 
            icon={<Insights />} 
            label="Insights" 
            id="faang-tab-2"
            aria-controls="faang-tabpanel-2"
          />
          {correlations && (
            <Tab 
              icon={<Star />} 
              label="Correlations" 
              id="faang-tab-3"
              aria-controls="faang-tabpanel-3"
            />
          )}
        </Tabs>
      </Box>

      {/* Overview Tab */}
      <TabPanel value={activeTab} index={0}>
        {summary ? (
          <AnalyticsSummaryCard summary={summary} />
        ) : (
          <Alert severity="info">
            FAANG summary data is not available. This may be due to company names not matching the dataset.
          </Alert>
        )}
      </TabPanel>

      {/* Comparison Tab */}
      <TabPanel value={activeTab} index={1}>
        {comparison ? (
          <CompanyComparisonChart comparison={comparison} />
        ) : (
          <Alert severity="info">
            FAANG comparison data is not available. This may be due to company names not matching the dataset.
          </Alert>
        )}
      </TabPanel>

      {/* Insights Tab */}
      <TabPanel value={activeTab} index={2}>
        {insights ? (
          <AnalyticsInsightsPanel insights={insights} />
        ) : (
          <Alert severity="info">
            FAANG insights are not available. This may be due to company names not matching the dataset.
          </Alert>
        )}
      </TabPanel>

      {/* Correlations Tab */}
      {correlations && (
        <TabPanel value={activeTab} index={3}>
          <CorrelationMatrix correlations={correlations} />
        </TabPanel>
      )}

      {/* FAANG-Specific Recommendations */}
      <Card sx={{ mt: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Major Tech Companies Interview Preparation Tips
          </Typography>
          <Box sx={{ 
            display: 'grid', 
            gridTemplateColumns: { xs: '1fr', md: 'repeat(2, 1fr)' }, 
            gap: 2 
          }}>
            <Alert severity="success" sx={{ mb: 2 }}>
              <Typography variant="subtitle2" gutterBottom>
                Focus Areas for Major Tech Companies
              </Typography>
              <Typography variant="body2">
                • System Design (especially for senior roles)<br/>
                • Data Structures & Algorithms<br/>
                • Behavioral questions (leadership principles)<br/>
                • Company-specific technologies and culture
              </Typography>
            </Alert>
            
            <Alert severity="info" sx={{ mb: 2 }}>
              <Typography variant="subtitle2" gutterBottom>
                Common Tech Company Topics
              </Typography>
              <Typography variant="body2">
                Based on the analysis, focus on:<br/>
                {summary?.topTopics.slice(0, 4).map(topic => topic.topic).join(', ')}
              </Typography>
            </Alert>
          </Box>
        </CardContent>
      </Card>
    </Box>
  );
};