import React, { useState } from 'react';
import {
  Box,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Chip,
  OutlinedInput,
  Button,
  Paper,
  Typography,
  Slider,
  Collapse
} from '@mui/material';
import {
  Search as SearchIcon,
  FilterList as FilterIcon,
  Clear as ClearIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon
} from '@mui/icons-material';
import type { CompanyFilterCriteria } from '../../types/company';

interface CompanyFiltersProps {
  filters: CompanyFilterCriteria;
  onFiltersChange: (filters: CompanyFilterCriteria) => void;
  onClearFilters: () => void;
  totalCompanies: number;
  filteredCount: number;
}

const DIFFICULTY_OPTIONS = [
  { value: 'EASY', label: 'Easy', color: '#4caf50' },
  { value: 'MEDIUM', label: 'Medium', color: '#ff9800' },
  { value: 'HARD', label: 'Hard', color: '#f44336' }
] as const;

const SORT_OPTIONS = [
  { value: 'company', label: 'Company Name' },
  { value: 'totalProblems', label: 'Total Problems' },
  { value: 'avgFrequency', label: 'Average Frequency' },
  { value: 'rank', label: 'Rank' }
] as const;

export function CompanyFilters({
  filters,
  onFiltersChange,
  onClearFilters,
  totalCompanies,
  filteredCount
}: CompanyFiltersProps) {
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [problemRange, setProblemRange] = useState<[number, number]>([
    filters.minProblems || 0,
    filters.maxProblems || 1000
  ]);

  const handleSearchChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    onFiltersChange({
      ...filters,
      searchQuery: event.target.value || undefined
    });
  };

  const handleDifficultyChange = (event: any) => {
    const value = event.target.value as string[];
    onFiltersChange({
      ...filters,
      difficulties: value.length > 0 ? value as ('EASY' | 'MEDIUM' | 'HARD')[] : undefined
    });
  };

  const handleSortChange = (field: 'sortBy' | 'sortOrder', value: string) => {
    onFiltersChange({
      ...filters,
      [field]: value
    });
  };

  const handleProblemRangeChange = (_event: Event, newValue: number | number[]) => {
    const range = newValue as [number, number];
    setProblemRange(range);
  };

  const handleProblemRangeCommitted = (_event: Event | React.SyntheticEvent, newValue: number | number[]) => {
    const range = newValue as [number, number];
    onFiltersChange({
      ...filters,
      minProblems: range[0] > 0 ? range[0] : undefined,
      maxProblems: range[1] < 1000 ? range[1] : undefined
    });
  };

  const hasActiveFilters = !!(
    filters.searchQuery ||
    filters.difficulties?.length ||
    filters.minProblems ||
    filters.maxProblems
  );

  return (
    <Paper sx={{ p: 3, mb: 3 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
        <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center' }}>
          <FilterIcon sx={{ mr: 1 }} />
          Filters
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Showing {filteredCount} of {totalCompanies} companies
        </Typography>
      </Box>

      <Box sx={{ 
        display: 'grid', 
        gridTemplateColumns: { 
          xs: '1fr', 
          md: '2fr 1fr 1fr' 
        }, 
        gap: 3 
      }}>
        {/* Search */}
        <TextField
          fullWidth
          placeholder="Search companies..."
          value={filters.searchQuery || ''}
          onChange={handleSearchChange}
          InputProps={{
            startAdornment: <SearchIcon sx={{ mr: 1, color: 'text.secondary' }} />
          }}
        />

        {/* Sort By */}
        <FormControl fullWidth>
          <InputLabel>Sort By</InputLabel>
          <Select
            value={filters.sortBy || 'totalProblems'}
            label="Sort By"
            onChange={(e) => handleSortChange('sortBy', e.target.value)}
          >
            {SORT_OPTIONS.map((option) => (
              <MenuItem key={option.value} value={option.value}>
                {option.label}
              </MenuItem>
            ))}
          </Select>
        </FormControl>

        {/* Sort Order */}
        <FormControl fullWidth>
          <InputLabel>Order</InputLabel>
          <Select
            value={filters.sortOrder || 'desc'}
            label="Order"
            onChange={(e) => handleSortChange('sortOrder', e.target.value)}
          >
            <MenuItem value="asc">Ascending</MenuItem>
            <MenuItem value="desc">Descending</MenuItem>
          </Select>
        </FormControl>
      </Box>

      {/* Advanced Filters Toggle */}
      <Box sx={{ mt: 2, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <Button
          startIcon={showAdvanced ? <ExpandLessIcon /> : <ExpandMoreIcon />}
          onClick={() => setShowAdvanced(!showAdvanced)}
          variant="text"
          size="small"
        >
          Advanced Filters
        </Button>
        
        {hasActiveFilters && (
          <Button
            startIcon={<ClearIcon />}
            onClick={onClearFilters}
            variant="outlined"
            size="small"
            color="secondary"
          >
            Clear Filters
          </Button>
        )}
      </Box>

      {/* Advanced Filters */}
      <Collapse in={showAdvanced}>
        <Box sx={{ mt: 3 }}>
          <Box sx={{ 
            display: 'grid', 
            gridTemplateColumns: { 
              xs: '1fr', 
              md: '1fr 1fr' 
            }, 
            gap: 3 
          }}>
            {/* Difficulty Filter */}
            <FormControl fullWidth>
              <InputLabel>Difficulties</InputLabel>
              <Select
                multiple
                value={filters.difficulties || []}
                onChange={handleDifficultyChange}
                input={<OutlinedInput label="Difficulties" />}
                renderValue={(selected) => (
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                    {selected.map((value) => {
                      const option = DIFFICULTY_OPTIONS.find(opt => opt.value === value);
                      return (
                        <Chip
                          key={value}
                          label={option?.label}
                          size="small"
                          sx={{ 
                            backgroundColor: option?.color,
                            color: 'white',
                            '& .MuiChip-deleteIcon': { color: 'white' }
                          }}
                        />
                      );
                    })}
                  </Box>
                )}
              >
                {DIFFICULTY_OPTIONS.map((option) => (
                  <MenuItem key={option.value} value={option.value}>
                    <Box sx={{ display: 'flex', alignItems: 'center' }}>
                      <Box
                        sx={{
                          width: 12,
                          height: 12,
                          backgroundColor: option.color,
                          borderRadius: '50%',
                          mr: 1
                        }}
                      />
                      {option.label}
                    </Box>
                  </MenuItem>
                ))}
              </Select>
            </FormControl>

            {/* Problem Count Range */}
            <Box>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                Problem Count Range: {problemRange[0]} - {problemRange[1]}
              </Typography>
              <Slider
                value={problemRange}
                onChange={handleProblemRangeChange}
                onChangeCommitted={handleProblemRangeCommitted}
                valueLabelDisplay="auto"
                min={0}
                max={1000}
                step={10}
                marks={[
                  { value: 0, label: '0' },
                  { value: 250, label: '250' },
                  { value: 500, label: '500' },
                  { value: 750, label: '750' },
                  { value: 1000, label: '1000+' }
                ]}
              />
            </Box>
          </Box>
        </Box>
      </Collapse>
    </Paper>
  );
}