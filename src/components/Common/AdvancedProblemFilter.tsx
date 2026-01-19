import React, { useState } from 'react';
import {
  Box,
  Paper,
  Typography,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Chip,
  Slider,
  Switch,
  FormControlLabel,
  Button,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Divider
} from '@mui/material';
import {
  ExpandMore as ExpandMoreIcon,
  FilterList as FilterListIcon,
  Clear as ClearIcon,
  Search as SearchIcon
} from '@mui/icons-material';
import type { ProblemData } from '../../types';

export interface ProblemFilterCriteria {
  searchQuery?: string;
  difficulties?: string[];
  topics?: string[];
  companies?: string[];
  frequencyRange?: [number, number];
  acceptanceRateRange?: [number, number];
  originalityScoreRange?: [number, number];
  likesRange?: [number, number];
  totalVotesRange?: [number, number];
  qualityTiers?: string[];
  hasQualityMetrics?: boolean;
  hasOfficialSolution?: boolean;
  hasVideoSolution?: boolean;
  isPaidOnly?: boolean;
}

interface AdvancedProblemFilterProps {
  problems: ProblemData[];
  onFilterChange: (criteria: ProblemFilterCriteria) => void;
  initialCriteria?: ProblemFilterCriteria;
}

const DIFFICULTY_OPTIONS = ['EASY', 'MEDIUM', 'HARD', 'UNKNOWN'];
const QUALITY_TIER_OPTIONS = [
  { value: 'hidden-gem', label: '💎 Hidden Gems' },
  { value: 'rising-star', label: '⭐ Rising Stars' },
  { value: 'interview-classic', label: '🏆 Interview Classics' },
  { value: 'controversial', label: '⚠️ Controversial' },
  { value: 'standard', label: 'Standard' }
];

const POPULAR_TOPICS = [
  'Array', 'String', 'Hash Table', 'Dynamic Programming', 'Math',
  'Depth-First Search', 'Breadth-First Search', 'Tree', 'Binary Search',
  'Two Pointers', 'Greedy', 'Stack', 'Heap (Priority Queue)', 'Graph',
  'Sliding Window', 'Backtracking', 'Divide and Conquer', 'Bit Manipulation'
];

export const AdvancedProblemFilter: React.FC<AdvancedProblemFilterProps> = ({
  problems,
  onFilterChange,
  initialCriteria = {}
}) => {
  const [criteria, setCriteria] = useState<ProblemFilterCriteria>(initialCriteria);
  const [expanded, setExpanded] = useState<string | false>('basic');

  // Extract unique values from problems
  const uniqueCompanies = React.useMemo(() => {
    const companies = new Set<string>();
    problems.forEach(problem => {
      if (problem.company) companies.add(problem.company);
    });
    return Array.from(companies).sort();
  }, [problems]);

  // Get ranges for sliders
  const ranges = React.useMemo(() => {
    const companyCounts = problems
      .map(p => (typeof p.companyCount === 'number' ? p.companyCount : 0))
      .filter(count => count > 0);
    const acceptanceRates = problems.map(p => p.acceptanceRate || 0).filter(r => r > 0);
    const originalityScores = problems.map(p => p.originalityScore || 0).filter(s => s > 0);
    const likes = problems.map(p => p.likes || 0).filter(l => l > 0);
    const totalVotes = problems.map(p => p.totalVotes || 0).filter(v => v > 0);

    return {
      companyCount: companyCounts.length > 0 ? [Math.min(...companyCounts), Math.max(...companyCounts)] : [0, 10],
      acceptanceRate: acceptanceRates.length > 0 ? [Math.min(...acceptanceRates), Math.max(...acceptanceRates)] : [0, 1],
      originalityScore: originalityScores.length > 0 ? [Math.min(...originalityScores), Math.max(...originalityScores)] : [0, 1],
      likes: likes.length > 0 ? [Math.min(...likes), Math.max(...likes)] : [0, 1000],
      totalVotes: totalVotes.length > 0 ? [Math.min(...totalVotes), Math.max(...totalVotes)] : [0, 10000]
    };
  }, [problems]);

  const handleCriteriaChange = (newCriteria: Partial<ProblemFilterCriteria>) => {
    const updated = { ...criteria, ...newCriteria };
    setCriteria(updated);
    onFilterChange(updated);
  };

  const handleReset = () => {
    const resetCriteria: ProblemFilterCriteria = {};
    setCriteria(resetCriteria);
    onFilterChange(resetCriteria);
  };

  const getActiveFilterCount = () => {
    let count = 0;
    if (criteria.searchQuery) count++;
    if (criteria.difficulties?.length) count++;
    if (criteria.topics?.length) count++;
    if (criteria.companies?.length) count++;
    if (criteria.qualityTiers?.length) count++;
    if (criteria.frequencyRange) count++;
    if (criteria.acceptanceRateRange) count++;
    if (criteria.originalityScoreRange) count++;
    if (criteria.likesRange) count++;
    if (criteria.totalVotesRange) count++;
    if (criteria.hasQualityMetrics) count++;
    if (criteria.hasOfficialSolution) count++;
    if (criteria.hasVideoSolution) count++;
    if (criteria.isPaidOnly !== undefined) count++;
    return count;
  };

  return (
    <Paper sx={{ p: 2 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <FilterListIcon />
          <Typography variant="h6">
            Advanced Filters
          </Typography>
          {getActiveFilterCount() > 0 && (
            <Chip 
              label={`${getActiveFilterCount()} active`} 
              size="small" 
              color="primary" 
            />
          )}
        </Box>
        <Button
          startIcon={<ClearIcon />}
          onClick={handleReset}
          disabled={getActiveFilterCount() === 0}
        >
          Reset All
        </Button>
      </Box>

      {/* Basic Filters */}
      <Accordion 
        expanded={expanded === 'basic'} 
        onChange={(_, isExpanded) => setExpanded(isExpanded ? 'basic' : false)}
      >
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
          <Typography variant="subtitle1">Basic Filters</Typography>
        </AccordionSummary>
        <AccordionDetails>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            <TextField
              fullWidth
              label="Search Problems"
              placeholder="Search by title, topic, or company..."
              value={criteria.searchQuery || ''}
              onChange={(e) => handleCriteriaChange({ searchQuery: e.target.value })}
              InputProps={{
                startAdornment: <SearchIcon sx={{ mr: 1, color: 'text.secondary' }} />
              }}
            />
            
            <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
              <FormControl sx={{ minWidth: 200, flex: 1 }}>
                <InputLabel>Difficulties</InputLabel>
                <Select
                  multiple
                  value={criteria.difficulties || []}
                  onChange={(e) => handleCriteriaChange({ difficulties: e.target.value as string[] })}
                  renderValue={(selected) => (
                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                      {(selected as string[]).map((value) => (
                        <Chip key={value} label={value} size="small" />
                      ))}
                    </Box>
                  )}
                >
                  {DIFFICULTY_OPTIONS.map(difficulty => (
                    <MenuItem key={difficulty} value={difficulty}>
                      {difficulty}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
              
              <FormControl sx={{ minWidth: 200, flex: 1 }}>
                <InputLabel>Quality Tiers</InputLabel>
                <Select
                  multiple
                  value={criteria.qualityTiers || []}
                  onChange={(e) => handleCriteriaChange({ qualityTiers: e.target.value as string[] })}
                  renderValue={(selected) => (
                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                      {(selected as string[]).map((value) => {
                        const tier = QUALITY_TIER_OPTIONS.find(t => t.value === value);
                        return <Chip key={value} label={tier?.label || value} size="small" />;
                      })}
                    </Box>
                  )}
                >
                  {QUALITY_TIER_OPTIONS.map(tier => (
                    <MenuItem key={tier.value} value={tier.value}>
                      {tier.label}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Box>
          </Box>
        </AccordionDetails>
      </Accordion>

      {/* Advanced Filters */}
      <Accordion 
        expanded={expanded === 'advanced'} 
        onChange={(_, isExpanded) => setExpanded(isExpanded ? 'advanced' : false)}
      >
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
          <Typography variant="subtitle1">Advanced Filters</Typography>
        </AccordionSummary>
        <AccordionDetails>
          <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
            <FormControl sx={{ minWidth: 200, flex: 1 }}>
              <InputLabel>Topics</InputLabel>
              <Select
                multiple
                value={criteria.topics || []}
                onChange={(e) => handleCriteriaChange({ topics: e.target.value as string[] })}
                renderValue={(selected) => (
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                    {(selected as string[]).slice(0, 3).map((value) => (
                      <Chip key={value} label={value} size="small" />
                    ))}
                    {(selected as string[]).length > 3 && (
                      <Chip label={`+${(selected as string[]).length - 3} more`} size="small" />
                    )}
                  </Box>
                )}
              >
                {POPULAR_TOPICS.map(topic => (
                  <MenuItem key={topic} value={topic}>
                    {topic}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
            
            <FormControl sx={{ minWidth: 200, flex: 1 }}>
              <InputLabel>Companies</InputLabel>
              <Select
                multiple
                value={criteria.companies || []}
                onChange={(e) => handleCriteriaChange({ companies: e.target.value as string[] })}
                renderValue={(selected) => (
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                    {(selected as string[]).slice(0, 2).map((value) => (
                      <Chip key={value} label={value} size="small" />
                    ))}
                    {(selected as string[]).length > 2 && (
                      <Chip label={`+${(selected as string[]).length - 2} more`} size="small" />
                    )}
                  </Box>
                )}
              >
                {uniqueCompanies.slice(0, 20).map(company => (
                  <MenuItem key={company} value={company}>
                    {company}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Box>
        </AccordionDetails>
      </Accordion>

      {/* Quality Metrics */}
      <Accordion 
        expanded={expanded === 'quality'} 
        onChange={(_, isExpanded) => setExpanded(isExpanded ? 'quality' : false)}
      >
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
          <Typography variant="subtitle1">Quality Metrics</Typography>
        </AccordionSummary>
        <AccordionDetails>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
            <FormControlLabel
              control={
                <Switch
                  checked={criteria.hasQualityMetrics || false}
                  onChange={(e) => handleCriteriaChange({ hasQualityMetrics: e.target.checked })}
                />
              }
              label="Only show problems with quality metrics"
            />
            
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 3 }}>
              <Box sx={{ minWidth: 250, flex: 1 }}>
                <Typography gutterBottom>
                  Originality Score: {criteria.originalityScoreRange ? 
                    `${(criteria.originalityScoreRange[0] * 100).toFixed(0)}% - ${(criteria.originalityScoreRange[1] * 100).toFixed(0)}%` : 
                    'All'
                  }
                </Typography>
                <Slider
                  value={criteria.originalityScoreRange || [ranges.originalityScore[0], ranges.originalityScore[1]]}
                  onChange={(_, value) => handleCriteriaChange({ originalityScoreRange: value as [number, number] })}
                  min={ranges.originalityScore[0]}
                  max={ranges.originalityScore[1]}
                  step={0.05}
                  valueLabelDisplay="auto"
                  valueLabelFormat={(value) => `${(value * 100).toFixed(0)}%`}
                />
              </Box>
              
              <Box sx={{ minWidth: 250, flex: 1 }}>
                <Typography gutterBottom>
                  Likes: {criteria.likesRange ? 
                    `${criteria.likesRange[0]} - ${criteria.likesRange[1]}` : 
                    'All'
                  }
                </Typography>
                <Slider
                  value={criteria.likesRange || [ranges.likes[0], ranges.likes[1]]}
                  onChange={(_, value) => handleCriteriaChange({ likesRange: value as [number, number] })}
                  min={ranges.likes[0]}
                  max={Math.min(ranges.likes[1], 5000)} // Cap for better UX
                  step={10}
                  valueLabelDisplay="auto"
                />
              </Box>
            </Box>
            
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 3 }}>
              <Box sx={{ minWidth: 250, flex: 1 }}>
                <Typography gutterBottom>
                  Total Votes: {criteria.totalVotesRange ? 
                    `${criteria.totalVotesRange[0]} - ${criteria.totalVotesRange[1]}` : 
                    'All'
                  }
                </Typography>
                <Slider
                  value={criteria.totalVotesRange || [ranges.totalVotes[0], ranges.totalVotes[1]]}
                  onChange={(_, value) => handleCriteriaChange({ totalVotesRange: value as [number, number] })}
                  min={ranges.totalVotes[0]}
                  max={Math.min(ranges.totalVotes[1], 20000)} // Cap for better UX
                  step={100}
                  valueLabelDisplay="auto"
                />
              </Box>
              
              <Box sx={{ minWidth: 250, flex: 1 }}>
                <Typography gutterBottom>
                  Acceptance Rate: {criteria.acceptanceRateRange ? 
                    `${(criteria.acceptanceRateRange[0] * 100).toFixed(0)}% - ${(criteria.acceptanceRateRange[1] * 100).toFixed(0)}%` : 
                    'All'
                  }
                </Typography>
                <Slider
                  value={criteria.acceptanceRateRange || [ranges.acceptanceRate[0], ranges.acceptanceRate[1]]}
                  onChange={(_, value) => handleCriteriaChange({ acceptanceRateRange: value as [number, number] })}
                  min={ranges.acceptanceRate[0]}
                  max={ranges.acceptanceRate[1]}
                  step={0.01}
                  valueLabelDisplay="auto"
                  valueLabelFormat={(value) => `${(value * 100).toFixed(0)}%`}
                />
              </Box>
            </Box>
          </Box>
          
          <Divider sx={{ my: 2 }} />
          
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2 }}>
            <FormControlLabel
              control={
                <Switch
                  checked={criteria.hasOfficialSolution || false}
                  onChange={(e) => handleCriteriaChange({ hasOfficialSolution: e.target.checked })}
                />
              }
              label="Has Official Solution"
            />
            
            <FormControlLabel
              control={
                <Switch
                  checked={criteria.hasVideoSolution || false}
                  onChange={(e) => handleCriteriaChange({ hasVideoSolution: e.target.checked })}
                />
              }
              label="Has Video Solution"
            />
            
            <FormControlLabel
              control={
                <Switch
                  checked={criteria.isPaidOnly || false}
                  onChange={(e) => handleCriteriaChange({ isPaidOnly: e.target.checked })}
                />
              }
              label="Premium Only"
            />
          </Box>
        </AccordionDetails>
      </Accordion>
    </Paper>
  );
};

export default AdvancedProblemFilter;
