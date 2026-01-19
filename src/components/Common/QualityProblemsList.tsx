import React, { useState, useMemo } from 'react';
import {
  Box,
  Typography,
  Paper,
  Button,
  Chip,
  Alert,
  FormControlLabel,
  Switch,
  Divider
} from '@mui/material';
import {
  FilterList as FilterListIcon
} from '@mui/icons-material';
import type { ProblemData } from '../../types';
import { ProblemsTable } from '../Tables/ProblemsTable';
import { AdvancedProblemFilter, type ProblemFilterCriteria } from './AdvancedProblemFilter';
import { ProblemPreviewDrawer } from './ProblemPreviewDrawer';

interface QualityProblemsListProps {
  problems: ProblemData[];
  title?: string;
  showFilters?: boolean;
  defaultShowQualityMetrics?: boolean;
  maxHeight?: number;
}

const getQualityTier = (problem: ProblemData): string => {
  if (!problem.originalityScore || !problem.totalVotes || !problem.likes) {
    return 'standard';
  }

  const { originalityScore, totalVotes, likes } = problem;
  
  if (originalityScore > 0.85 && totalVotes < 1000 && likes > 50) {
    return 'hidden-gem';
  }
  
  if (originalityScore > 0.8 && totalVotes >= 1000 && totalVotes <= 5000 && likes > 100) {
    return 'rising-star';
  }
  
  if (likes > 1000 && totalVotes > 5000) {
    return 'interview-classic';
  }
  
  if (originalityScore < 0.7) {
    return 'controversial';
  }
  
  return 'standard';
};

const filterProblems = (problems: ProblemData[], criteria: ProblemFilterCriteria): ProblemData[] => {
  return problems.filter(problem => {
    // Search query
    if (criteria.searchQuery) {
      const query = criteria.searchQuery.toLowerCase();
      const matchesTitle = problem.title.toLowerCase().includes(query);
      const matchesCompany = problem.company?.toLowerCase().includes(query);
      const matchesTopics = problem.topics?.some(topic => 
        topic.toLowerCase().includes(query)
      );
      
      if (!matchesTitle && !matchesCompany && !matchesTopics) {
        return false;
      }
    }
    
    // Difficulties
    if (criteria.difficulties?.length && !criteria.difficulties.includes(problem.difficulty)) {
      return false;
    }
    
    // Topics
    if (criteria.topics?.length) {
      const hasMatchingTopic = problem.topics?.some(topic => 
        criteria.topics!.some(filterTopic => 
          topic.toLowerCase().includes(filterTopic.toLowerCase())
        )
      );
      if (!hasMatchingTopic) return false;
    }
    
    // Companies
    if (criteria.companies?.length && problem.company) {
      if (!criteria.companies.includes(problem.company)) {
        return false;
      }
    }
    
    // Quality tiers
    if (criteria.qualityTiers?.length) {
      const problemTier = getQualityTier(problem);
      if (!criteria.qualityTiers.includes(problemTier)) {
        return false;
      }
    }
    
    // Quality metrics requirement
    if (criteria.hasQualityMetrics) {
      if (!problem.originalityScore || !problem.likes || !problem.totalVotes) {
        return false;
      }
    }
    
    // Company coverage range (reuse frequency slider)
    if (criteria.frequencyRange && typeof problem.companyCount === 'number') {
      const [min, max] = criteria.frequencyRange;
      if (problem.companyCount < min || problem.companyCount > max) {
        return false;
      }
    }
    
    // Acceptance rate range
    if (criteria.acceptanceRateRange && problem.acceptanceRate) {
      const [min, max] = criteria.acceptanceRateRange;
      if (problem.acceptanceRate < min || problem.acceptanceRate > max) {
        return false;
      }
    }
    
    // Originality score range
    if (criteria.originalityScoreRange && problem.originalityScore) {
      const [min, max] = criteria.originalityScoreRange;
      if (problem.originalityScore < min || problem.originalityScore > max) {
        return false;
      }
    }
    
    // Likes range
    if (criteria.likesRange && problem.likes) {
      const [min, max] = criteria.likesRange;
      if (problem.likes < min || problem.likes > max) {
        return false;
      }
    }
    
    // Total votes range
    if (criteria.totalVotesRange && problem.totalVotes) {
      const [min, max] = criteria.totalVotesRange;
      if (problem.totalVotes < min || problem.totalVotes > max) {
        return false;
      }
    }
    
    // Solution availability
    if (criteria.hasOfficialSolution && !problem.hasOfficialSolution) {
      return false;
    }
    
    if (criteria.hasVideoSolution && !problem.hasVideoSolution) {
      return false;
    }
    
    // Premium status
    if (criteria.isPaidOnly !== undefined && problem.isPaidOnly !== criteria.isPaidOnly) {
      return false;
    }
    
    return true;
  });
};

export const QualityProblemsList: React.FC<QualityProblemsListProps> = ({
  problems,
  title = "Problems List",
  showFilters = true,
  defaultShowQualityMetrics = true,
  maxHeight = 600
}) => {
  const [filterCriteria, setFilterCriteria] = useState<ProblemFilterCriteria>({});
  const [showFilterPanel, setShowFilterPanel] = useState(false);
  const [showQualityMetrics, setShowQualityMetrics] = useState(defaultShowQualityMetrics);
  const [showQualityBadges, setShowQualityBadges] = useState(true);
  const [selectedProblem, setSelectedProblem] = useState<ProblemData | null>(null);
  const [previewOpen, setPreviewOpen] = useState(false);
  
  // Filter problems based on criteria
  const filteredProblems = useMemo(() => {
    return filterProblems(problems, filterCriteria);
  }, [problems, filterCriteria]);

  const handleProblemSelect = (problem: ProblemData) => {
    setSelectedProblem(problem);
    setPreviewOpen(true);
  };

  const handlePreviewClose = () => {
    setPreviewOpen(false);
    setSelectedProblem(null);
  };
  
  // Get quality statistics
  const qualityStats = useMemo(() => {
    const withQuality = problems.filter(p => p.originalityScore && p.likes && p.totalVotes);
    const tiers = {
      'hidden-gem': 0,
      'rising-star': 0,
      'interview-classic': 0,
      'controversial': 0,
      'standard': 0
    };
    
    withQuality.forEach(problem => {
      const tier = getQualityTier(problem);
      tiers[tier as keyof typeof tiers]++;
    });
    
    return {
      total: problems.length,
      withQuality: withQuality.length,
      tiers,
      avgOriginality: withQuality.length > 0 
        ? withQuality.reduce((sum, p) => sum + (p.originalityScore || 0), 0) / withQuality.length
        : 0
    };
  }, [problems]);
  
  const getActiveFilterCount = () => {
    let count = 0;
    if (filterCriteria.searchQuery) count++;
    if (filterCriteria.difficulties?.length) count++;
    if (filterCriteria.topics?.length) count++;
    if (filterCriteria.companies?.length) count++;
    if (filterCriteria.qualityTiers?.length) count++;
    return count;
  };

  return (
    <Box>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Box>
          <Typography variant="h5" gutterBottom>
            {title}
          </Typography>
          <Box sx={{ display: 'flex', gap: 1, alignItems: 'center', flexWrap: 'wrap' }}>
            <Typography variant="body2" color="text.secondary">
              {filteredProblems.length} of {problems.length} problems
            </Typography>
            {qualityStats.withQuality > 0 && (
              <>
                <Divider orientation="vertical" flexItem />
                <Typography variant="body2" color="text.secondary">
                  {qualityStats.withQuality} with quality metrics
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Avg quality: {(qualityStats.avgOriginality * 100).toFixed(1)}%
                </Typography>
              </>
            )}
          </Box>
        </Box>
        
        <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
          {showFilters && (
            <Button
              variant={showFilterPanel ? "contained" : "outlined"}
              startIcon={<FilterListIcon />}
              onClick={() => setShowFilterPanel(!showFilterPanel)}
            >
              Filters {getActiveFilterCount() > 0 && `(${getActiveFilterCount()})`}
            </Button>
          )}
        </Box>
      </Box>
      
      {/* Quality Overview */}
      {qualityStats.withQuality > 0 && (
        <Paper sx={{ p: 2, mb: 2 }}>
          <Typography variant="subtitle2" gutterBottom>
            Quality Distribution
          </Typography>
          <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
            {Object.entries(qualityStats.tiers).map(([tier, count]) => {
              if (count === 0) return null;
              
              const config = {
                'hidden-gem': { label: '💎 Hidden Gems', color: 'success' as const },
                'rising-star': { label: '⭐ Rising Stars', color: 'info' as const },
                'interview-classic': { label: '🏆 Classics', color: 'warning' as const },
                'controversial': { label: '⚠️ Controversial', color: 'error' as const },
                'standard': { label: 'Standard', color: 'default' as const }
              };
              
              const { label, color } = config[tier as keyof typeof config];
              
              return (
                <Chip
                  key={tier}
                  label={`${label}: ${count}`}
                  color={color}
                  size="small"
                  onClick={() => {
                    setFilterCriteria(prev => ({
                      ...prev,
                      qualityTiers: [tier]
                    }));
                  }}
                  sx={{ cursor: 'pointer' }}
                />
              );
            })}
          </Box>
        </Paper>
      )}
      
      {/* Filter Panel */}
      {showFilters && showFilterPanel && (
        <Box sx={{ mb: 2 }}>
          <AdvancedProblemFilter
            problems={problems}
            onFilterChange={setFilterCriteria}
            initialCriteria={filterCriteria}
          />
        </Box>
      )}
      
      {/* Display Options */}
      <Paper sx={{ p: 2, mb: 2 }}>
        <Box sx={{ display: 'flex', gap: 2, alignItems: 'center', flexWrap: 'wrap' }}>
          <FormControlLabel
            control={
              <Switch
                checked={showQualityMetrics}
                onChange={(e) => setShowQualityMetrics(e.target.checked)}
              />
            }
            label="Show Quality Metrics"
          />
          <FormControlLabel
            control={
              <Switch
                checked={showQualityBadges}
                onChange={(e) => setShowQualityBadges(e.target.checked)}
              />
            }
            label="Show Quality Badges"
          />
        </Box>
      </Paper>
      
      {/* Results */}
      {filteredProblems.length === 0 ? (
        <Alert severity="info">
          No problems match your current filters. Try adjusting the criteria to see more results.
        </Alert>
      ) : (
        <ProblemsTable
          problems={filteredProblems}
          maxHeight={maxHeight}
          showQualityMetrics={showQualityMetrics}
          showQualityBadges={showQualityBadges}
          onProblemSelect={handleProblemSelect}
        />
      )}
      <ProblemPreviewDrawer
        open={previewOpen}
        problem={selectedProblem}
        onClose={handlePreviewClose}
      />
    </Box>
  );
};

export default QualityProblemsList;
