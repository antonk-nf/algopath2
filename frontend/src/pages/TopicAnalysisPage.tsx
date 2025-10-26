import {
  Box,
  Typography,
  Card,
  CardContent,
  Alert,
  Chip,
  Button,
  TextField,
  InputAdornment,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TableSortLabel,
  IconButton,
  Tooltip
} from '@mui/material';
import {
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  TrendingFlat as TrendingFlatIcon,
  Insights as InsightsIcon,
  WarningAmber as WarningIcon,
  Refresh as RefreshIcon,
  Search as SearchIcon,
  Clear as ClearIcon,
  FilterList as FilterIcon
} from '@mui/icons-material';
import { useTopicData } from '../hooks/useTopicData';
import { LoadingSpinner } from '../components/Common/LoadingSpinner';
import { useEffect, useMemo, useState } from 'react';

function getTrendIcon(direction?: string) {
  switch ((direction || '').toLowerCase()) {
    case 'up':
    case 'rising':
    case 'positive':
    case 'increasing':
      return <TrendingUpIcon color="success" />;
    case 'down':
    case 'falling':
    case 'negative':
    case 'decreasing':
      return <TrendingDownIcon color="error" />;
    case 'insufficient_data':
      return <TrendingFlatIcon color="disabled" />;
    default:
      return <TrendingFlatIcon color="action" />;
  }
}

function formatTrendStrength(strength?: number) {
  if (strength === undefined || Number.isNaN(strength)) {
    return '—';
  }
  return `${(strength * 100).toFixed(1)}%`;
}

type SortField = 'topic' | 'totalFrequency' | 'trendStrength';
type SortOrder = 'asc' | 'desc';

export function TopicAnalysisPage() {
  const {
    trends,
    trendsLoading,
    trendsError,
    refreshTrends
  } = useTopicData(50);

  const [searchQuery, setSearchQuery] = useState('');
  const [trendFilter, setTrendFilter] = useState('');
  const [sortField, setSortField] = useState<SortField>('totalFrequency');
  const [sortOrder, setSortOrder] = useState<SortOrder>('desc');
  const [showAllTrends, setShowAllTrends] = useState(false);

  const filteredAndSortedTrends = useMemo(() => {
    const filtered = trends.filter(trend => {
      const matchesSearch = trend.topic.toLowerCase().includes(searchQuery.toLowerCase());
      const matchesTrend = !trendFilter || trend.trendDirection?.toLowerCase().includes(trendFilter.toLowerCase());
      return matchesSearch && matchesTrend;
    });

    return filtered.sort((a, b) => {
      let aValue: any;
      let bValue: any;
      switch (sortField) {
        case 'topic':
          aValue = a.topic.toLowerCase();
          bValue = b.topic.toLowerCase();
          break;
        case 'totalFrequency':
          aValue = a.totalFrequency ?? 0;
          bValue = b.totalFrequency ?? 0;
          break;
        case 'trendStrength':
          aValue = a.trendStrength ?? 0;
          bValue = b.trendStrength ?? 0;
          break;
        default:
          aValue = 0;
          bValue = 0;
      }

      if (aValue < bValue) return sortOrder === 'asc' ? -1 : 1;
      if (aValue > bValue) return sortOrder === 'asc' ? 1 : -1;
      return 0;
    });
  }, [trends, searchQuery, trendFilter, sortField, sortOrder]);

  const trendsToDisplay = useMemo(() => (
    showAllTrends
      ? filteredAndSortedTrends
      : filteredAndSortedTrends.slice(0, 10)
  ), [filteredAndSortedTrends, showAllTrends]);

  const filteredTrendCount = filteredAndSortedTrends.length;

  useEffect(() => {
    if (showAllTrends && filteredTrendCount <= 10) {
      setShowAllTrends(false);
    }
  }, [filteredTrendCount, showAllTrends]);

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortOrder('desc');
    }
  };

  const clearFilters = () => {
    setSearchQuery('');
    setTrendFilter('');
  };

  return (
    <Box>
      <Typography variant="h4" component="h1" gutterBottom>
        Topic Analysis Dashboard
      </Typography>

      <Typography variant="body1" color="text.secondary" sx={{ mb: 4 }}>
        Explore trending LeetCode topics and analyze which skills are gaining momentum across companies.
        Search, filter, and sort topics to focus on what matters most for your interview preparation.
      </Typography>

      <Card sx={{ mb: 4 }}>
        <CardContent>
          <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
            <FilterIcon sx={{ mr: 1 }} />
            Search & Filter Topics
          </Typography>

          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2 }}>
              <Box sx={{ flex: '1 1 300px', minWidth: '250px' }}>
                <TextField
                  fullWidth
                  label="Search Topics"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  InputProps={{
                    startAdornment: (
                      <InputAdornment position="start">
                        <SearchIcon />
                      </InputAdornment>
                    ),
                    endAdornment: searchQuery && (
                      <InputAdornment position="end">
                        <IconButton size="small" onClick={() => setSearchQuery('')}>
                          <ClearIcon />
                        </IconButton>
                      </InputAdornment>
                    ),
                  }}
                  placeholder="e.g., Array, Dynamic Programming"
                />
              </Box>

              <Box sx={{ flex: '1 1 200px', minWidth: '180px' }}>
                <FormControl fullWidth>
                  <InputLabel>Trend Direction</InputLabel>
                  <Select
                    value={trendFilter}
                    label="Trend Direction"
                    onChange={(e) => setTrendFilter(e.target.value)}
                  >
                    <MenuItem value="">All Trends</MenuItem>
                    <MenuItem value="increasing">Increasing</MenuItem>
                    <MenuItem value="decreasing">Decreasing</MenuItem>
                    <MenuItem value="insufficient_data">Insufficient Data</MenuItem>
                    <MenuItem value="stable">Stable</MenuItem>
                  </Select>
                </FormControl>
              </Box>

              <Box sx={{ flex: '0 0 150px' }}>
                <Button
                  fullWidth
                  variant="outlined"
                  onClick={clearFilters}
                  startIcon={<ClearIcon />}
                  sx={{ height: '56px' }}
                >
                  Clear Filters
                </Button>
              </Box>
            </Box>
          </Box>
        </CardContent>
      </Card>

      <Card sx={{ mb: 4 }}>
        <CardContent>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
            <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center' }}>
              <InsightsIcon sx={{ mr: 1 }} />
              Topic Trends Analysis
            </Typography>
            <Button
              size="small"
              startIcon={<RefreshIcon />}
              onClick={refreshTrends}
              disabled={trendsLoading}
            >
              Refresh Data
            </Button>
          </Box>

          {trendsLoading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
              <LoadingSpinner message="Analyzing topic trends..." />
            </Box>
          ) : trendsError ? (
            <Alert severity="warning" icon={<WarningIcon />} sx={{ mb: 2 }}>
              {trendsError}
            </Alert>
          ) : filteredAndSortedTrends.length === 0 ? (
            <Alert severity="info">
              {trends.length === 0
                ? 'No trending topics available right now. Try refreshing later.'
                : 'No topics match your current filters. Try adjusting your search criteria.'}
            </Alert>
          ) : (
            <TableContainer component={Paper} variant="outlined">
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>
                      <TableSortLabel
                        active={sortField === 'topic'}
                        direction={sortField === 'topic' ? sortOrder : 'asc'}
                        onClick={() => handleSort('topic')}
                      >
                        Topic
                      </TableSortLabel>
                    </TableCell>
                    <TableCell align="center">Trend</TableCell>
                    <TableCell align="right">
                      <TableSortLabel
                        active={sortField === 'totalFrequency'}
                        direction={sortField === 'totalFrequency' ? sortOrder : 'desc'}
                        onClick={() => handleSort('totalFrequency')}
                      >
                        Total Frequency
                      </TableSortLabel>
                    </TableCell>
                    <TableCell align="right">
                      <TableSortLabel
                        active={sortField === 'trendStrength'}
                        direction={sortField === 'trendStrength' ? sortOrder : 'desc'}
                        onClick={() => handleSort('trendStrength')}
                      >
                        Trend Strength
                      </TableSortLabel>
                    </TableCell>
                    <TableCell align="center">Timeframe Buckets</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {trendsToDisplay.map((trend, index) => {
                    const directionValue = typeof trend.trendDirection === 'string'
                      ? trend.trendDirection
                      : 'insufficient_data';
                    const direction = directionValue || 'stable';
                    const directionLower = direction.toLowerCase();
                    const strengthLabel = formatTrendStrength(trend.trendStrength);
                    const totalFrequency = trend.totalFrequency ?? 0;
                    const timeframeCount = trend.validTimeframeCount ?? trend.timeframeCount ?? 0;

                    return (
                      <TableRow key={`${trend.topic}-${index}`} hover>
                        <TableCell>
                          <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
                            {trend.topic}
                          </Typography>
                        </TableCell>
                        <TableCell align="center">
                          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                            {getTrendIcon(direction)}
                            <Chip
                              label={direction.replace(/_/g, ' ').toUpperCase()}
                              color={directionLower.includes('increas')
                                ? 'success'
                                : directionLower.includes('decreas')
                                  ? 'error'
                                  : directionLower.includes('insufficient')
                                    ? 'default'
                                    : 'default'}
                              variant="outlined"
                              size="small"
                              sx={{ ml: 1 }}
                            />
                          </Box>
                        </TableCell>
                        <TableCell align="right">
                          <Typography variant="body2" sx={{ fontWeight: 500 }}>
                            {totalFrequency.toLocaleString()}
                          </Typography>
                        </TableCell>
                        <TableCell align="right">
                          <Typography variant="body2">
                            {strengthLabel}
                          </Typography>
                        </TableCell>
                        <TableCell align="center">
                          <Tooltip title="Number of timeframe buckets (30d, 3m, 6m, etc.) with enough data to evaluate the trend">
                            <Chip label={timeframeCount} size="small" variant="outlined" />
                          </Tooltip>
                        </TableCell>
                      </TableRow>
                    );
                  })}
                </TableBody>
              </Table>
            </TableContainer>
          )}

          {!trendsLoading && !trendsError && filteredTrendCount > 10 && (
            <Box sx={{ display: 'flex', justifyContent: 'center', mt: 2 }}>
              <Button
                variant="outlined"
                onClick={() => setShowAllTrends((prev) => !prev)}
              >
                {showAllTrends
                  ? 'Show top 10 rows'
                  : `Show all (${filteredTrendCount})`}
              </Button>
            </Box>
          )}

        </CardContent>
      </Card>
    </Box>
  );
}
