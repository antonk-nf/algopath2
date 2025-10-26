import React, { useState, useMemo } from 'react';
import {
  Box,
  Typography,
  Paper,
  Slider,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Chip,
  Button,
  Card,
  CardContent,
  CardActions,
  IconButton,
  Tooltip,
  Alert
} from '@mui/material';
import {
  FilterList as FilterIcon,
  Bookmark as BookmarkIcon,
  Launch as LaunchIcon
} from '@mui/icons-material';
import type { HiddenGemsFilter, ProblemData } from '../../types';

interface HiddenGemsFinderProps {
  problems: ProblemData[];
  onProblemSelect?: (problem: ProblemData) => void;
  onBookmark?: (problem: ProblemData) => void;
}

const DIFFICULTY_OPTIONS = ['EASY', 'MEDIUM', 'HARD'] as const;
const TOPIC_OPTIONS = [
  'Arrays', 'Dynamic Programming', 'Trees', 'Graphs', 'Hash Tables',
  'Strings', 'Linked Lists', 'Binary Search', 'Sorting', 'Two Pointers'
];

interface ProblemCardProps {
  problem: ProblemData;
  onSelect?: (problem: ProblemData) => void;
  onBookmark?: (problem: ProblemData) => void;
}

const ProblemCard: React.FC<ProblemCardProps> = ({ problem, onSelect, onBookmark }) => {
  const originalityScore = (problem as any).originalityScore || 0;
  const likes = (problem as any).likes || 0;
  const totalVotes = (problem as any).totalVotes || 0;

  return (
    <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <CardContent sx={{ flexGrow: 1 }}>
        <Typography variant="h6" gutterBottom>
          {problem.title}
        </Typography>
        
        <Box sx={{ display: 'flex', gap: 1, mb: 2, flexWrap: 'wrap' }}>
          <Chip 
            label={problem.difficulty} 
            size="small"
            color={
              problem.difficulty === 'EASY' ? 'success' :
              problem.difficulty === 'MEDIUM' ? 'warning' :
              problem.difficulty === 'HARD' ? 'error' : 'default'
            }
          />
          <Chip label={problem.company} size="small" variant="outlined" />
        </Box>
        
        <Typography variant="body2" color="text.secondary" gutterBottom>
          Topics: {problem.topics.join(', ')}
        </Typography>
        
        {originalityScore > 0 && (
          <Box sx={{ mt: 2 }}>
            <Typography variant="caption" display="block">
              Originality: {(originalityScore * 100).toFixed(1)}%
            </Typography>
            <Typography variant="caption" display="block">
              Likes: {likes.toLocaleString()} | Votes: {totalVotes.toLocaleString()}
            </Typography>
          </Box>
        )}
      </CardContent>
      
      <CardActions>
        <Button size="small" onClick={() => onSelect?.(problem)}>
          View Details
        </Button>
        <Tooltip title="Bookmark">
          <IconButton size="small" onClick={() => onBookmark?.(problem)}>
            <BookmarkIcon />
          </IconButton>
        </Tooltip>
        {problem.link && (
          <Tooltip title="Open Problem">
            <IconButton 
              size="small" 
              component="a" 
              href={problem.link} 
              target="_blank"
              rel="noopener noreferrer"
            >
              <LaunchIcon />
            </IconButton>
          </Tooltip>
        )}
      </CardActions>
    </Card>
  );
};

export const HiddenGemsFinder: React.FC<HiddenGemsFinderProps> = ({
  problems,
  onProblemSelect,
  onBookmark
}) => {
  const [filters, setFilters] = useState<HiddenGemsFilter>({
    minOriginalityScore: 0.85,
    maxTotalVotes: 2000,
    minLikes: 50,
    difficulties: [],
    topics: [],
    companies: []
  });

  const [showFilters, setShowFilters] = useState(false);

  // Filter problems based on criteria
  const filteredProblems = useMemo(() => {
    return problems.filter(problem => {
      const originalityScore = (problem as any).originalityScore || 0;
      const likes = (problem as any).likes || 0;
      const totalVotes = (problem as any).totalVotes || 0;

      // Apply quality filters
      if (originalityScore < (filters.minOriginalityScore || 0.85)) return false;
      if (totalVotes > (filters.maxTotalVotes || 2000)) return false;
      if (likes < (filters.minLikes || 50)) return false;

      // Apply difficulty filter
      if (filters.difficulties && filters.difficulties.length > 0) {
        if (problem.difficulty === 'UNKNOWN' || !filters.difficulties.includes(problem.difficulty as 'EASY' | 'MEDIUM' | 'HARD')) {
          return false;
        }
      }

      // Apply topic filter
      if (filters.topics && filters.topics.length > 0) {
        const hasMatchingTopic = problem.topics?.some(topic => 
          filters.topics!.includes(topic)
        );
        if (!hasMatchingTopic) return false;
      }

      // Apply company filter
      if (filters.companies && filters.companies.length > 0) {
        if (!problem.company || !filters.companies.includes(problem.company)) {
          return false;
        }
      }

      return true;
    }).sort((a, b) => {
      // Sort by originality score descending, then by likes descending
      const aOriginality = (a as any).originalityScore || 0;
      const bOriginality = (b as any).originalityScore || 0;
      if (bOriginality !== aOriginality) {
        return bOriginality - aOriginality;
      }
      
      const aLikes = (a as any).likes || 0;
      const bLikes = (b as any).likes || 0;
      return bLikes - aLikes;
    });
  }, [problems, filters]);

  // Categorize problems
  const categorizedProblems = useMemo(() => {
    const categories = {
      'hidden-gem': [] as ProblemData[],
      'rising-star': [] as ProblemData[],
      'controversial': [] as ProblemData[]
    };

    filteredProblems.forEach(problem => {
      const originalityScore = (problem as any).originalityScore || 0;
      const likes = (problem as any).likes || 0;
      const dislikes = (problem as any).dislikes || 0;
      const totalVotes = (problem as any).totalVotes || 0;

      // Hidden gems: high originality, low exposure
      if (originalityScore >= 0.85 && totalVotes <= 2000 && likes >= 50) {
        categories['hidden-gem'].push(problem);
      }
      // Rising stars: good originality, moderate exposure, growing
      else if (originalityScore >= 0.8 && totalVotes >= 1000 && totalVotes <= 5000) {
        categories['rising-star'].push(problem);
      }
      // Controversial: mixed reactions
      else if (dislikes > 0 && (dislikes / Math.max(likes, 1)) > 0.3) {
        categories['controversial'].push(problem);
      }
    });

    return categories;
  }, [filteredProblems]);

  return (
    <Box>
      <Typography variant="h5" gutterBottom>
        Hidden Gems Finder
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        Discover high-quality problems with low community exposure
      </Typography>

      {/* Filter Toggle */}
      <Button
        startIcon={<FilterIcon />}
        onClick={() => setShowFilters(!showFilters)}
        sx={{ mb: 2 }}
      >
        {showFilters ? 'Hide Filters' : 'Show Filters'}
      </Button>

      {/* Filters Panel */}
      {showFilters && (
        <Paper sx={{ p: 3, mb: 3 }}>
          <Typography variant="h6" gutterBottom>
            Quality Filters
          </Typography>
          
          <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: 'repeat(3, 1fr)' }, gap: 3, mb: 3 }}>
            <Box>
              <Typography gutterBottom>
                Minimum Originality Score: {(filters.minOriginalityScore || 0.8) * 100}%
              </Typography>
              <Slider
                value={filters.minOriginalityScore || 0.8}
                onChange={(_, value) => setFilters(prev => ({ 
                  ...prev, 
                  minOriginalityScore: value as number 
                }))}
                min={0.5}
                max={1}
                step={0.05}
                marks={[
                  { value: 0.5, label: '50%' },
                  { value: 0.85, label: '85%' },
                  { value: 1, label: '100%' }
                ]}
              />
            </Box>
            
            <Box>
              <Typography gutterBottom>
                Maximum Total Votes: {(filters.maxTotalVotes || 2000).toLocaleString()}
              </Typography>
              <Slider
                value={filters.maxTotalVotes || 2000}
                onChange={(_, value) => setFilters(prev => ({ 
                  ...prev, 
                  maxTotalVotes: value as number 
                }))}
                min={100}
                max={5000}
                step={100}
                marks={[
                  { value: 100, label: '100' },
                  { value: 2000, label: '2K' },
                  { value: 5000, label: '5K' }
                ]}
              />
            </Box>
            
            <Box>
              <Typography gutterBottom>
                Minimum Likes: {filters.minLikes || 50}
              </Typography>
              <Slider
                value={filters.minLikes || 50}
                onChange={(_, value) => setFilters(prev => ({ 
                  ...prev, 
                  minLikes: value as number 
                }))}
                min={10}
                max={500}
                step={10}
                marks={[
                  { value: 10, label: '10' },
                  { value: 50, label: '50' },
                  { value: 500, label: '500' }
                ]}
              />
            </Box>
          </Box>
          
          <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: '1fr 1fr' }, gap: 3 }}>
            <FormControl fullWidth>
              <InputLabel>Difficulties</InputLabel>
              <Select
                multiple
                value={filters.difficulties || []}
                onChange={(e) => setFilters(prev => ({ 
                  ...prev, 
                  difficulties: e.target.value as ('EASY' | 'MEDIUM' | 'HARD')[]
                }))}
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
            
            <FormControl fullWidth>
              <InputLabel>Topics</InputLabel>
              <Select
                multiple
                value={filters.topics || []}
                onChange={(e) => setFilters(prev => ({ 
                  ...prev, 
                  topics: e.target.value as string[] 
                }))}
                renderValue={(selected) => (
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                    {(selected as string[]).map((value) => (
                      <Chip key={value} label={value} size="small" />
                    ))}
                  </Box>
                )}
              >
                {TOPIC_OPTIONS.map(topic => (
                  <MenuItem key={topic} value={topic}>
                    {topic}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Box>
        </Paper>
      )}

      {/* Results Summary */}
      <Alert severity="info" sx={{ mb: 3 }}>
        Found {filteredProblems.length} problems matching your criteria:
        {' '}
        {categorizedProblems['hidden-gem'].length} hidden gems,
        {' '}
        {categorizedProblems['rising-star'].length} rising stars,
        {' '}
        {categorizedProblems['controversial'].length} controversial problems
      </Alert>

      {/* Problem Categories */}
      {Object.entries(categorizedProblems).map(([category, categoryProblems]) => (
        categoryProblems.length > 0 && (
          <Box key={category} sx={{ mb: 4 }}>
            <Typography variant="h6" gutterBottom sx={{ textTransform: 'capitalize' }}>
              {category.replace('-', ' ')} ({categoryProblems.length})
            </Typography>
            
            <Box sx={{ 
              display: 'grid', 
              gridTemplateColumns: { xs: '1fr', md: 'repeat(2, 1fr)', lg: 'repeat(3, 1fr)' }, 
              gap: 2 
            }}>
              {categoryProblems.slice(0, 6).map(problem => (
                <ProblemCard
                  key={problem.title}
                  problem={problem}
                  onSelect={onProblemSelect}
                  onBookmark={onBookmark}
                />
              ))}
            </Box>
            
            {categoryProblems.length > 6 && (
              <Button sx={{ mt: 2 }}>
                View All {categoryProblems.length} {category.replace('-', ' ')}
              </Button>
            )}
          </Box>
        )
      ))}

      {filteredProblems.length === 0 && (
        <Alert severity="warning">
          No problems match your current filters. Try adjusting the criteria to find more results.
        </Alert>
      )}
    </Box>
  );
};

export default HiddenGemsFinder;