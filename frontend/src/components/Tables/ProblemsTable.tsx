import React, { useState, useMemo } from 'react';
import {
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TableSortLabel,
  Paper,
  Chip,
  Link,
  Box,
  Typography,
  IconButton,
  Tooltip
} from '@mui/material';
import {
  OpenInNew as OpenInNewIcon,
  Diamond as DiamondIcon,
  Star as StarIcon,
  Warning as WarningIcon,
  EmojiEvents as TrophyIcon,
  Groups as GroupsIcon,
  InfoOutlined as InfoIcon
} from '@mui/icons-material';
import type { ProblemData } from '../../types/company';
import BookmarkButton from '../Common/BookmarkButton';

interface ProblemsTableProps {
  problems: ProblemData[];
  maxHeight?: number;
  showQualityMetrics?: boolean;
  showQualityBadges?: boolean;
  showBookmarks?: boolean;
  onProblemSelect?: (problem: ProblemData) => void;
}

type SortField = 'title' | 'difficulty' | 'companyCount' | 'frequency' | 'originalityScore' | 'likes' | 'totalVotes';
type SortOrder = 'asc' | 'desc';

const getQualityTier = (problem: ProblemData): string => {
  if (!problem.originalityScore || !problem.totalVotes || !problem.likes) {
    return 'standard';
  }

  const { originalityScore, totalVotes, likes } = problem;
  
  // Hidden Gems: High originality (>0.85), low exposure (<1000 votes), decent likes (>50)
  if (originalityScore > 0.85 && totalVotes < 1000 && likes > 50) {
    return 'hidden-gem';
  }
  
  // Rising Stars: High originality (>0.8), moderate exposure (1000-5000), growing likes
  if (originalityScore > 0.8 && totalVotes >= 1000 && totalVotes <= 5000 && likes > 100) {
    return 'rising-star';
  }
  
  // Interview Classics: High likes (>1000), high exposure (>5000)
  if (likes > 1000 && totalVotes > 5000) {
    return 'interview-classic';
  }
  
  // Controversial: Low originality (<0.7)
  if (originalityScore < 0.7) {
    return 'controversial';
  }
  
  return 'standard';
};

const QualityBadge: React.FC<{ tier: string; size?: 'small' | 'medium' }> = ({ tier, size = 'small' }) => {
  const config = {
    'hidden-gem': { icon: <DiamondIcon />, color: '#4CAF50', label: 'Hidden Gem' },
    'rising-star': { icon: <StarIcon />, color: '#2196F3', label: 'Rising Star' },
    'interview-classic': { icon: <TrophyIcon />, color: '#FF9800', label: 'Classic' },
    'controversial': { icon: <WarningIcon />, color: '#F44336', label: 'Controversial' },
    'standard': { icon: null, color: '#9E9E9E', label: 'Standard' }
  };
  
  const { icon, color, label } = config[tier as keyof typeof config] || config.standard;
  
  if (!icon) return null;
  
  return (
    <Tooltip title={label}>
      <Box sx={{ color, display: 'inline-flex', alignItems: 'center' }}>
        {React.cloneElement(icon, { fontSize: size })}
      </Box>
    </Tooltip>
  );
};

export function ProblemsTable({ 
  problems, 
  maxHeight = 400, 
  showQualityBadges = false,
  showBookmarks = true,
  onProblemSelect
}: ProblemsTableProps) {
  const [sortField, setSortField] = useState<SortField>('frequency');
  const [sortOrder, setSortOrder] = useState<SortOrder>('desc');

  // Sort problems based on current sort field and order
  const sortedProblems = useMemo(() => {
    return [...problems].sort((a, b) => {
      let aValue: any = a[sortField];
      let bValue: any = b[sortField];

      // Handle difficulty sorting
      if (sortField === 'difficulty') {
        const difficultyOrder = { 'EASY': 1, 'MEDIUM': 2, 'HARD': 3, 'UNKNOWN': 4 };
        aValue = difficultyOrder[a.difficulty];
        bValue = difficultyOrder[b.difficulty];
      }

      // Handle quality metrics - treat undefined as 0
      if (sortField === 'originalityScore' || sortField === 'likes' || sortField === 'totalVotes' || sortField === 'companyCount' || sortField === 'frequency') {
        aValue = aValue || 0;
        bValue = bValue || 0;
      }

      // Handle string sorting
      if (typeof aValue === 'string' && typeof bValue === 'string') {
        aValue = aValue.toLowerCase();
        bValue = bValue.toLowerCase();
      }

      if (aValue < bValue) {
        return sortOrder === 'asc' ? -1 : 1;
      }
      if (aValue > bValue) {
        return sortOrder === 'asc' ? 1 : -1;
      }
      return 0;
    });
  }, [problems, sortField, sortOrder]);

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortOrder('desc');
    }
  };

  const getDifficultyColor = (difficulty: string) => {
    switch (difficulty) {
      case 'EASY': return 'success';
      case 'MEDIUM': return 'warning';
      case 'HARD': return 'error';
      default: return 'default';
    }
  };

  const formatFrequency = (value?: number) => {
    if (typeof value !== 'number' || Number.isNaN(value)) {
      return '—';
    }
    return value.toFixed(1);
  };

  if (problems.length === 0) {
    return (
      <Paper sx={{ p: 4, textAlign: 'center' }}>
        <Typography variant="body1" color="text.secondary">
          No problems data available
        </Typography>
      </Paper>
    );
  }

  return (
    <TableContainer 
      component={Paper} 
      sx={{ 
        maxHeight,
        '& .MuiTableCell-head': {
          backgroundColor: 'grey.50',
          fontWeight: 'bold'
        }
      }}
    >
      <Table stickyHeader size="small">
        <TableHead>
          <TableRow>
            <TableCell>
              <TableSortLabel
                active={sortField === 'title'}
                direction={sortField === 'title' ? sortOrder : 'asc'}
                onClick={() => handleSort('title')}
              >
                Problem Title
              </TableSortLabel>
            </TableCell>
            <TableCell align="center">
              <TableSortLabel
                active={sortField === 'difficulty'}
                direction={sortField === 'difficulty' ? sortOrder : 'asc'}
                onClick={() => handleSort('difficulty')}
              >
                Difficulty
              </TableSortLabel>
            </TableCell>
            <TableCell align="center">
              <TableSortLabel
                active={sortField === 'companyCount'}
                direction={sortField === 'companyCount' ? sortOrder : 'desc'}
                onClick={() => handleSort('companyCount')}
              >
                  <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                    <GroupsIcon sx={{ mr: 0.5, fontSize: 16 }} />
                    Companies Asked
                  </Box>
              </TableSortLabel>
            </TableCell>
            <TableCell align="center">
              <TableSortLabel
                active={sortField === 'frequency'}
                direction={sortField === 'frequency' ? sortOrder : 'desc'}
                onClick={() => handleSort('frequency')}
              >
                Frequency
              </TableSortLabel>
            </TableCell>
            <TableCell>Topics</TableCell>
            <TableCell align="center">Actions</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {sortedProblems.map((problem, index) => (
            <TableRow 
              key={`${problem.title}-${index}`}
              hover
              role={onProblemSelect ? 'button' : undefined}
              tabIndex={onProblemSelect ? 0 : -1}
              onClick={onProblemSelect ? () => onProblemSelect(problem) : undefined}
              onKeyDown={onProblemSelect ? (event) => {
                if (event.key === 'Enter' || event.key === ' ') {
                  event.preventDefault();
                  onProblemSelect(problem);
                }
              } : undefined}
              sx={{
                cursor: onProblemSelect ? 'pointer' : 'default',
                '&:last-child td, &:last-child th': { border: 0 },
                outline: 'none'
              }}
            >
              <TableCell>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <Box sx={{ flexGrow: 1 }}>
                    <Typography variant="body2" sx={{ fontWeight: 500 }}>
                      {problem.title}
                    </Typography>
                    {problem.company && (
                      <Typography variant="caption" color="text.secondary">
                        {problem.company}
                      </Typography>
                    )}
                  </Box>
                  {showQualityBadges && (
                    <QualityBadge tier={getQualityTier(problem)} />
                  )}
                </Box>
              </TableCell>
              <TableCell align="center">
                <Chip
                  label={problem.difficulty}
                  color={getDifficultyColor(problem.difficulty) as any}
                  size="small"
                  variant="outlined"
                />
              </TableCell>
              <TableCell align="center">
                <Typography variant="body2" sx={{ fontWeight: 500 }}>
                  {typeof problem.companyCount === 'number'
                    ? problem.companyCount.toLocaleString()
                    : '—'}
                </Typography>
              </TableCell>
              <TableCell align="center">
                <Typography variant="body2" sx={{ fontWeight: 500 }}>
                  {formatFrequency(problem.frequency)}
                </Typography>
              </TableCell>
              <TableCell>
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, maxWidth: 200 }}>
                  {problem.topics.slice(0, 3).map((topic) => (
                    <Chip
                      key={topic}
                      label={topic}
                      size="small"
                      variant="outlined"
                      sx={{ fontSize: '0.7rem', height: 20 }}
                    />
                  ))}
                  {problem.topics.length > 3 && (
                    <Tooltip title={problem.topics.slice(3).join(', ')}>
                      <Chip
                        label={`+${problem.topics.length - 3}`}
                        size="small"
                        variant="outlined"
                        sx={{ fontSize: '0.7rem', height: 20 }}
                      />
                    </Tooltip>
                  )}
                </Box>
              </TableCell>
              <TableCell align="center">
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 0.5 }}>
                  {onProblemSelect && (
                    <Tooltip title="View details">
                      <IconButton
                        size="small"
                        onClick={(event) => {
                          event.stopPropagation();
                          onProblemSelect(problem);
                        }}
                      >
                        <InfoIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                  )}
                  {showBookmarks && (
                    <BookmarkButton problem={problem} size="small" />
                  )}
                  {problem.link && (
                    <IconButton
                      component={Link}
                      href={problem.link}
                      target="_blank"
                      rel="noopener noreferrer"
                      size="small"
                      color="primary"
                      onClick={(event) => event.stopPropagation()}
                    >
                      <OpenInNewIcon fontSize="small" />
                    </IconButton>
                  )}
                </Box>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  );
}
