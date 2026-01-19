import {
  Box,
  TextField,
  InputAdornment,
  IconButton,
  Chip,
  Typography,
  Paper,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  Divider,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Button,
  Collapse
} from '@mui/material';
import {
  Search as SearchIcon,
  Clear as ClearIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon
} from '@mui/icons-material';
import { useState, useMemo, useCallback } from 'react';
import { TopicTrendIndicator } from './TopicTrendIndicator';
import type { TopicTrend, TopicFrequency } from '../../types/topic';

interface TopicSearchProps {
  topics: (TopicTrend | TopicFrequency)[];
  onTopicSelect?: (topic: string) => void;
  onFilterChange?: (filters: TopicSearchFilters) => void;
  placeholder?: string;
  showFilters?: boolean;
  maxResults?: number;
}

export interface TopicSearchFilters {
  query: string;
  trendDirection?: string;
  minFrequency?: number;
  sortBy?: 'relevance' | 'frequency' | 'trend';
  sortOrder?: 'asc' | 'desc';
}

export function TopicSearch({
  topics,
  onTopicSelect,
  onFilterChange,
  placeholder = "Search topics (e.g., Array, Dynamic Programming, Graph)",
  showFilters = true,
  maxResults = 20
}: TopicSearchProps) {
  const [filters, setFilters] = useState<TopicSearchFilters>({
    query: '',
    sortBy: 'frequency',
    sortOrder: 'desc'
  });
  const [showAdvancedFilters, setShowAdvancedFilters] = useState(false);
  const [selectedTopics, setSelectedTopics] = useState<string[]>([]);

  // Extract unique trend directions for filter dropdown
  const availableTrends = useMemo(() => {
    const trends = new Set<string>();
    topics.forEach(topic => {
      if ('trendDirection' in topic && topic.trendDirection) {
        trends.add(topic.trendDirection);
      }
    });
    return Array.from(trends).sort();
  }, [topics]);

  // Search and filter logic
  const filteredTopics = useMemo(() => {
    let filtered = topics.filter(topic => {
      // Text search
      const matchesQuery = !filters.query || 
        topic.topic.toLowerCase().includes(filters.query.toLowerCase());

      // Trend filter
      const matchesTrend = !filters.trendDirection || 
        ('trendDirection' in topic && topic.trendDirection === filters.trendDirection);

      // Frequency filter
      const frequency = 'frequency' in topic ? topic.frequency : 
        ('totalFrequency' in topic ? topic.totalFrequency ?? 0 : 0);
      const matchesFrequency = !filters.minFrequency || frequency >= filters.minFrequency;

      return matchesQuery && matchesTrend && matchesFrequency;
    });

    // Sort results
    filtered.sort((a, b) => {
      let aValue: any, bValue: any;

      switch (filters.sortBy) {
        case 'frequency':
          aValue = 'frequency' in a ? a.frequency : (a.totalFrequency ?? 0);
          bValue = 'frequency' in b ? b.frequency : (b.totalFrequency ?? 0);
          break;
        case 'trend':
          aValue = 'trendStrength' in a ? (a.trendStrength ?? 0) : 0;
          bValue = 'trendStrength' in b ? (b.trendStrength ?? 0) : 0;
          break;
        case 'relevance':
        default:
          // For relevance, prioritize exact matches, then partial matches
          const queryLower = filters.query.toLowerCase();
          const aExact = a.topic.toLowerCase() === queryLower ? 1 : 0;
          const bExact = b.topic.toLowerCase() === queryLower ? 1 : 0;
          if (aExact !== bExact) return bExact - aExact;
          
          const aStarts = a.topic.toLowerCase().startsWith(queryLower) ? 1 : 0;
          const bStarts = b.topic.toLowerCase().startsWith(queryLower) ? 1 : 0;
          if (aStarts !== bStarts) return bStarts - aStarts;
          
          // Fall back to frequency
          aValue = 'frequency' in a ? a.frequency : (a.totalFrequency ?? 0);
          bValue = 'frequency' in b ? b.frequency : (b.totalFrequency ?? 0);
          break;
      }

      if (filters.sortOrder === 'asc') {
        return aValue < bValue ? -1 : aValue > bValue ? 1 : 0;
      } else {
        return aValue > bValue ? -1 : aValue < bValue ? 1 : 0;
      }
    });

    return filtered.slice(0, maxResults);
  }, [topics, filters, maxResults]);

  // Update filters and notify parent
  const updateFilters = useCallback((newFilters: Partial<TopicSearchFilters>) => {
    const updatedFilters = { ...filters, ...newFilters };
    setFilters(updatedFilters);
    onFilterChange?.(updatedFilters);
  }, [filters, onFilterChange]);

  // Handle topic selection
  const handleTopicSelect = (topic: string) => {
    if (!selectedTopics.includes(topic)) {
      setSelectedTopics([...selectedTopics, topic]);
    }
    onTopicSelect?.(topic);
  };

  // Remove selected topic
  const handleTopicRemove = (topic: string) => {
    setSelectedTopics(selectedTopics.filter(t => t !== topic));
  };

  // Clear all filters
  const clearFilters = () => {
    const clearedFilters: TopicSearchFilters = {
      query: '',
      sortBy: 'frequency',
      sortOrder: 'desc'
    };
    setFilters(clearedFilters);
    onFilterChange?.(clearedFilters);
  };

  return (
    <Box>
      {/* Main search input */}
      <TextField
        fullWidth
        value={filters.query}
        onChange={(e) => updateFilters({ query: e.target.value })}
        placeholder={placeholder}
        InputProps={{
          startAdornment: (
            <InputAdornment position="start">
              <SearchIcon />
            </InputAdornment>
          ),
          endAdornment: filters.query && (
            <InputAdornment position="end">
              <IconButton size="small" onClick={() => updateFilters({ query: '' })}>
                <ClearIcon />
              </IconButton>
            </InputAdornment>
          ),
        }}
        sx={{ mb: 2 }}
      />

      {/* Selected topics */}
      {selectedTopics.length > 0 && (
        <Box sx={{ mb: 2 }}>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
            Selected Topics:
          </Typography>
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
            {selectedTopics.map(topic => (
              <Chip
                key={topic}
                label={topic}
                onDelete={() => handleTopicRemove(topic)}
                color="primary"
                variant="outlined"
              />
            ))}
          </Box>
        </Box>
      )}

      {/* Filter controls */}
      {showFilters && (
        <Box sx={{ mb: 2 }}>
          <Button
            startIcon={showAdvancedFilters ? <ExpandLessIcon /> : <ExpandMoreIcon />}
            onClick={() => setShowAdvancedFilters(!showAdvancedFilters)}
            size="small"
            sx={{ mb: 1 }}
          >
            Advanced Filters
          </Button>
          
          <Collapse in={showAdvancedFilters}>
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2, p: 2, bgcolor: 'action.hover', borderRadius: 1 }}>
              <FormControl size="small" sx={{ minWidth: 120 }}>
                <InputLabel>Sort By</InputLabel>
                <Select
                  value={filters.sortBy}
                  label="Sort By"
                  onChange={(e) => updateFilters({ sortBy: e.target.value as any })}
                >
                  <MenuItem value="relevance">Relevance</MenuItem>
                  <MenuItem value="frequency">Frequency</MenuItem>
                  <MenuItem value="trend">Trend Strength</MenuItem>
                </Select>
              </FormControl>

              <FormControl size="small" sx={{ minWidth: 100 }}>
                <InputLabel>Order</InputLabel>
                <Select
                  value={filters.sortOrder}
                  label="Order"
                  onChange={(e) => updateFilters({ sortOrder: e.target.value as any })}
                >
                  <MenuItem value="desc">High to Low</MenuItem>
                  <MenuItem value="asc">Low to High</MenuItem>
                </Select>
              </FormControl>

              {availableTrends.length > 0 && (
                <FormControl size="small" sx={{ minWidth: 120 }}>
                  <InputLabel>Trend</InputLabel>
                  <Select
                    value={filters.trendDirection || ''}
                    label="Trend"
                    onChange={(e) => updateFilters({ trendDirection: e.target.value || undefined })}
                  >
                    <MenuItem value="">All Trends</MenuItem>
                    {availableTrends.map(trend => (
                      <MenuItem key={trend} value={trend}>
                        {trend.charAt(0).toUpperCase() + trend.slice(1)}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              )}

              <TextField
                size="small"
                type="number"
                label="Min Frequency"
                value={filters.minFrequency || ''}
                onChange={(e) => updateFilters({ 
                  minFrequency: e.target.value ? parseInt(e.target.value) : undefined 
                })}
                sx={{ width: 120 }}
              />

              <Button size="small" onClick={clearFilters} startIcon={<ClearIcon />}>
                Clear
              </Button>
            </Box>
          </Collapse>
        </Box>
      )}

      {/* Results summary */}
      <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
        {filteredTopics.length === maxResults ? `Showing top ${maxResults}` : `Found ${filteredTopics.length}`} 
        {filters.query && ` results for "${filters.query}"`}
      </Typography>

      {/* Search results */}
      <Paper variant="outlined" sx={{ maxHeight: 400, overflow: 'auto' }}>
        {filteredTopics.length === 0 ? (
          <Box sx={{ p: 3, textAlign: 'center' }}>
            <Typography variant="body2" color="text.secondary">
              {filters.query ? 'No topics match your search criteria' : 'Start typing to search topics'}
            </Typography>
          </Box>
        ) : (
          <List dense>
            {filteredTopics.map((topic, index) => {
              const frequency = 'frequency' in topic ? topic.frequency : (topic.totalFrequency ?? 0);
              const isSelected = selectedTopics.includes(topic.topic);
              
              return (
                <Box key={`${topic.topic}-${index}`}>
                  <ListItem
                    onClick={() => handleTopicSelect(topic.topic)}
                    sx={{
                      cursor: 'pointer',
                      backgroundColor: isSelected ? 'action.selected' : 'transparent',
                      '&:hover': {
                        backgroundColor: 'action.hover'
                      }
                    }}
                  >
                    <ListItemText
                      primary={
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <Typography variant="body2" sx={{ fontWeight: 500 }}>
                            {topic.topic}
                          </Typography>
                          {'trendDirection' in topic && topic.trendDirection && (
                            <TopicTrendIndicator
                              trendDirection={topic.trendDirection}
                              trendStrength={topic.trendStrength}
                              size="small"
                              variant="icon"
                            />
                          )}
                        </Box>
                      }
                      secondary={`Frequency: ${frequency.toLocaleString()}`}
                    />
                    <ListItemSecondaryAction>
                      {'trendDirection' in topic && (
                        <TopicTrendIndicator
                          trendDirection={topic.trendDirection}
                          trendStrength={topic.trendStrength}
                          size="small"
                          variant="chip"
                          showPercentage={true}
                        />
                      )}
                    </ListItemSecondaryAction>
                  </ListItem>
                  {index < filteredTopics.length - 1 && <Divider />}
                </Box>
              );
            })}
          </List>
        )}
      </Paper>
    </Box>
  );
}