
import { useState, useEffect, type ReactNode } from 'react';
import { 
  Box, 
  Typography, 
  Card, 
  CardContent,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip
} from '@mui/material';
import { 
  BarChart as BarChartIcon,
  Business as BusinessIcon,
  Quiz as QuizIcon,
  Topic as TopicIcon,
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  TrendingFlat as TrendingFlatIcon
} from '@mui/icons-material';
import { CompanyStatsChart, TopicFrequencyChart, TopicHeatmapChart } from '../components/Charts';
import { CompanyClusterCard } from '../components/Company';
import { LoadingSpinner } from '../components/Common/LoadingSpinner';
import { companyService } from '../services/companyService';
import { topicService } from '../services/topicService';
import type { CompanyData } from '../types/company';
import type { TopicFrequency, TopicTrend, TopicHeatmap } from '../types/topic';

interface SummaryTileProps {
  icon: ReactNode;
  label: string;
  value: number | string;
  annotation?: string;
  color?: 'primary' | 'secondary' | 'success' | 'warning';
}

function SummaryTile({ icon, label, value, annotation, color = 'primary' }: SummaryTileProps) {
  const formattedValue = typeof value === 'number'
    ? value % 1 === 0
      ? value.toLocaleString()
      : value.toLocaleString(undefined, { maximumFractionDigits: 1 })
    : value;

  return (
    <Card variant="outlined" sx={{ height: '100%' }}>
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 1.5 }}>
          <Box
            sx={{
              mr: 2,
              p: 1,
              display: 'inline-flex',
              borderRadius: 1,
              bgcolor: `${color}.light`,
              color: `${color}.dark`
            }}
          >
            {icon}
          </Box>
          <Typography variant="h5" component="div" sx={{ fontWeight: 600 }}>
            {formattedValue}
          </Typography>
        </Box>
        <Typography variant="body2" color="text.secondary">
          {label}
        </Typography>
        {annotation && (
          <Typography variant="caption" color="text.secondary">
            {annotation}
          </Typography>
        )}
      </CardContent>
    </Card>
  );
}

export function OverviewPage() {
  const [companies, setCompanies] = useState<CompanyData[]>([]);
  const [loading, setLoading] = useState(true);
  const [topicFrequencies, setTopicFrequencies] = useState<TopicFrequency[]>([]);
  const [topicTrends, setTopicTrends] = useState<TopicTrend[]>([]);
  const [trendsLoading, setTrendsLoading] = useState(true);
  const [heatmapData, setHeatmapData] = useState<TopicHeatmap | null>(null);
  const [heatmapAvailable, setHeatmapAvailable] = useState(false);
  const [heatmapError, setHeatmapError] = useState<string | null>(null);
  const [heatmapLoading, setHeatmapLoading] = useState(true);

  useEffect(() => {
    loadCompanies();
    loadTopicFrequencies();
    loadTopicTrends();
    loadTopicHeatmap();
  }, []);

  const loadCompanies = async () => {
    try {
      const companiesData = await companyService.getCompanyStats();
      setCompanies(companiesData);
    } catch (error) {
      console.error('Failed to load companies:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadTopicFrequencies = async () => {
    try {
      const frequencyData = await topicService.getTopicFrequency(20);
      setTopicFrequencies(frequencyData);
    } catch (error) {
      console.error('Failed to load topic frequency data:', error);
    }
  };

  const loadTopicTrends = async () => {
    try {
      setTrendsLoading(true);
      const trendsData = await topicService.getTopicTrends(50, {
        sortByAbs: true,
        disableCache: true
      });
      setTopicTrends(trendsData);
    } catch (error) {
      console.error('Failed to load topic trends data:', error);
    } finally {
      setTrendsLoading(false);
    }
  };

  const loadTopicHeatmap = async () => {
    const targetCompanies = [
      'Adobe',
      'Amazon',
      'Apple',
      'Airbnb',
      'Anduril',
      'Citadel',
      'Atlassian',
      'Goldman Sachs',
      'Accenture',
      'Capgemini',
      'Agoda',
      'Expedia'
    ];

    try {
      setHeatmapLoading(true);
      const data = await topicService.getTopicHeatmap(20, targetCompanies);
      if (data && data.topics?.length && data.companies?.length && Array.isArray(data.matrix) && data.matrix.length) {
        const filteredCompanies = [...targetCompanies];
        const filteredMatrix = data.matrix.map((row) =>
          filteredCompanies.map((company) => {
            const index = data.companies.indexOf(company);
            return index >= 0 ? row[index] ?? 0 : 0;
          })
        );
        const filteredCompanyTotals = Array.isArray(data.companyTotals)
          ? filteredCompanies.map((company) => {
              const index = data.companies.indexOf(company);
              return index >= 0 ? data.companyTotals![index] ?? 0 : 0;
            })
          : undefined;

        const missingCompanies = filteredCompanies.filter((company) => !data.companies.includes(company));

        const normalizedHeatmap = {
          ...data,
          companies: filteredCompanies,
          matrix: filteredMatrix,
          companyTotals: filteredCompanyTotals,
          metadata: {
            ...data.metadata,
            selected_companies: filteredCompanies
          }
        };

        setHeatmapData(normalizedHeatmap);
        setHeatmapAvailable(true);
        setHeatmapError(
          missingCompanies.length
            ? `No heatmap data returned for ${missingCompanies.join(', ')} — values default to 0.`
            : null
        );
      } else {
        throw new Error('Incomplete heatmap data');
      }
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Topic heatmap endpoint unavailable';
      setHeatmapError(message);
      setHeatmapAvailable(false);
      setHeatmapData(null);
    } finally {
      setHeatmapLoading(false);
    }
  };

  const stats = companyService.calculateStats(companies);
  const derivedMetrics = {
    totalCompanies: stats.totalCompanies,
    totalProblems: stats.totalProblems,
    avgProblemsPerCompany: stats.avgProblemsPerCompany,
    totalTopics: companyService.calculateUniqueTopics(companies),
    timeframeCoverage: companyService.calculateTimeframeCoverage(companies)
  };

  return (
    <Box>
      <Typography variant="h4" component="h1" gutterBottom>
        Welcome to Interview Prep Dashboard
      </Typography>
      
      <Typography variant="body1" color="text.secondary" sx={{ mb: 4 }}>
        Your comprehensive platform for data-driven interview preparation. 
        Leverage insights from 18,668+ LeetCode problems across 470+ companies 
        to prepare strategically for technical interviews.
      </Typography>

      <Stack spacing={3}>
        <Card>
          <CardContent>
            <Typography variant="h5" gutterBottom>
              Analytics Overview
            </Typography>
            {loading ? (
              <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
                <LoadingSpinner size={36} />
              </Box>
            ) : (
              <Box
                sx={{
                  display: 'grid',
                  gridTemplateColumns: {
                    xs: 'repeat(1, 1fr)',
                    sm: 'repeat(2, 1fr)',
                    lg: 'repeat(4, 1fr)'
                  },
                  gap: 3
                }}
              >
                <SummaryTile
                  icon={<BusinessIcon fontSize="medium" />}
                  label="Total Companies"
                  value={derivedMetrics.totalCompanies}
                  annotation="In dataset"
                  color="primary"
                />
                <SummaryTile
                  icon={<QuizIcon fontSize="medium" />}
                  label="Total Problems"
                  value={derivedMetrics.totalProblems}
                  annotation="Across dataset"
                  color="secondary"
                />
                <SummaryTile
                  icon={<TopicIcon fontSize="medium" />}
                  label="Total Topics"
                  value={derivedMetrics.totalTopics}
                  annotation="Unique topics covered"
                  color="success"
                />
                <SummaryTile
                  icon={<TrendingUpIcon fontSize="medium" />}
                  label="Avg per Company"
                  value={derivedMetrics.avgProblemsPerCompany}
                  annotation="Dataset average"
                  color="warning"
                />
              </Box>
            )}
          </CardContent>
        </Card>

        {/* Company Statistics Chart */}
        <Card>
          <CardContent>
            <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
              <BarChartIcon sx={{ mr: 1 }} />
              Top Companies by Problem Count
            </Typography>
            {loading ? (
              <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
                <LoadingSpinner message="Loading company statistics..." />
              </Box>
            ) : (
              <CompanyStatsChart companies={companies} height={400} maxCompanies={10} />
            )}
          </CardContent>
        </Card>

        <Card>
          <CardContent>
            <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>
              Frequency Overview
            </Typography>
            {topicFrequencies.length === 0 ? (
              <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
                <LoadingSpinner message="Loading topic frequency..." size={32} />
              </Box>
            ) : (
              <TopicFrequencyChart
                data={topicFrequencies}
                height={320}
                maxTopics={12}
                showTrendIndicators
              />
            )}
          </CardContent>
        </Card>

        <Card>
          <CardContent>
            <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>
              Topic Trends Analysis
            </Typography>
            {trendsLoading ? (
              <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
                <LoadingSpinner message="Analyzing topic trends..." size={32} />
              </Box>
            ) : topicTrends.length === 0 ? (
              <Typography variant="body2" color="text.secondary">
                Topic trend insights are not available right now.
              </Typography>
            ) : (
              <TableContainer component={Paper} variant="outlined">
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>Topic</TableCell>
                      <TableCell align="center">Trend</TableCell>
                      <TableCell align="right">Total Frequency</TableCell>
                      <TableCell align="right">Trend Strength</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {topicTrends.slice(0, 5).map((trend, index) => {
                      const rawStrength = typeof trend.trendStrength === 'number' ? trend.trendStrength : 0;
                      const absStrength = Math.abs(rawStrength);
                      const frequency = trend.totalFrequency ?? 0;

                      let direction: 'increasing' | 'decreasing' | 'stable';
                      if (absStrength < 0.001) {
                        direction = 'stable';
                      } else if (rawStrength > 0) {
                        direction = 'increasing';
                      } else {
                        direction = 'decreasing';
                      }

                      let icon = <TrendingFlatIcon color="action" fontSize="small" />;
                      let chipColor: 'default' | 'success' | 'error' = 'default';
                      if (direction === 'increasing') {
                        icon = <TrendingUpIcon color="success" fontSize="small" />;
                        chipColor = 'success';
                      } else if (direction === 'decreasing') {
                        icon = <TrendingDownIcon color="error" fontSize="small" />;
                        chipColor = 'error';
                      }

                      const chipLabel = direction.toUpperCase();

                      return (
                        <TableRow key={`${trend.topic}-${index}`}>
                          <TableCell sx={{ fontWeight: 500 }}>{trend.topic}</TableCell>
                          <TableCell align="center">
                            <Box sx={{ display: 'inline-flex', alignItems: 'center', gap: 1 }}>
                              {icon}
                              <Chip
                                label={chipLabel}
                                size="small"
                                variant="outlined"
                                color={chipColor}
                                sx={{
                                  borderColor:
                                    chipColor === 'success'
                                      ? 'success.main'
                                      : chipColor === 'error'
                                        ? 'error.main'
                                        : 'divider',
                                  color:
                                    chipColor === 'success'
                                      ? 'success.main'
                                      : chipColor === 'error'
                                        ? 'error.main'
                                        : 'text.secondary'
                                }}
                              />
                            </Box>
                          </TableCell>
                          <TableCell align="right">{frequency.toLocaleString()}</TableCell>
                          <TableCell align="right">{(rawStrength * 100).toFixed(2)}%</TableCell>
                        </TableRow>
                      );
                    })}
                  </TableBody>
                </Table>
              </TableContainer>
            )}
          </CardContent>
        </Card>

        <CompanyClusterCard />

        <Card>
          <CardContent>
            <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
              <BusinessIcon sx={{ mr: 1 }} />
              Topic-Company Heatmap
            </Typography>
            {heatmapLoading ? (
              <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
                <LoadingSpinner message="Loading topic heatmap..." />
              </Box>
            ) : heatmapAvailable && heatmapData ? (
              <>
                <TopicHeatmapChart
                  data={heatmapData}
                  height={520}
                  maxTopics={15}
                  maxCompanies={12}
                />
                {heatmapError && (
                  <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 2 }}>
                    {heatmapError}
                  </Typography>
                )}
              </>
            ) : (
              <Paper elevation={0} sx={{ p: 3, bgcolor: 'action.hover' }}>
                <Typography variant="body2" color="text.secondary">
                  {heatmapError || 'Topic heatmap visualization is not yet available.'}
                </Typography>
              </Paper>
            )}
          </CardContent>
        </Card>
      </Stack>
    </Box>
  );
}
