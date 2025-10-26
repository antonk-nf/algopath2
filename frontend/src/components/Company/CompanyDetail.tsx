
import { useState, useEffect, useCallback, useRef } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Chip,
  Button,
  Paper
} from '@mui/material';
import {
  ArrowBack as ArrowBackIcon,
  Business as BusinessIcon
} from '@mui/icons-material';
import { LoadingSpinner } from '../Common/LoadingSpinner';
import { ErrorMessage } from '../Common/ErrorMessage';
import { ProblemPreviewDrawer } from '../Common/ProblemPreviewDrawer';
import { ProblemsTable } from '../Tables';
import { companyService } from '../../services/companyService';
import type { CompanyData, ProblemData } from '../../types/company';

interface CompanyDetailProps {
  company: CompanyData | null;
  loading: boolean;
  error: string | null;
  onBack: () => void;
  onRetry?: () => void;
}

export function CompanyDetail({
  company,
  loading,
  error,
  onBack,
  onRetry
}: CompanyDetailProps) {
  const PAGE_SIZE = 25;

  const [problems, setProblems] = useState<ProblemData[]>([]);
  const [problemsTotal, setProblemsTotal] = useState(0);
  const [problemsOffset, setProblemsOffset] = useState(0);
  const [problemsHasMore, setProblemsHasMore] = useState(false);
  const [problemsLoading, setProblemsLoading] = useState(false);
  const [problemsLoadingMore, setProblemsLoadingMore] = useState(false);
  const [selectedProblem, setSelectedProblem] = useState<ProblemData | null>(null);
  const [previewOpen, setPreviewOpen] = useState(false);
  const [selectedTopicFilter, setSelectedTopicFilter] = useState<string | null>(null);
  const problemsOffsetRef = useRef(0);
  const loadProblemsRef = useRef<((params?: { reset?: boolean; topic?: string | null; offset?: number; forceRemote?: boolean }) => Promise<void>) | null>(null);

  useEffect(() => {
    problemsOffsetRef.current = problemsOffset;
  }, [problemsOffset]);

  const loadProblems = useCallback(
    async ({ reset = false, topic, offset, forceRemote = false }: { reset?: boolean; topic?: string | null; offset?: number; forceRemote?: boolean } = {}) => {
      if (!company) return;

      const effectiveTopic = topic !== undefined ? topic : selectedTopicFilter;
      const requestOffset = reset ? 0 : offset ?? problemsOffsetRef.current;

      if (reset) {
        setProblemsLoading(true);
        setProblemsOffset(0);
        setProblems([]);
      } else {
        setProblemsLoadingMore(true);
      }

      try {
        const result = await companyService.getCompanyProblems(company.company, {
          limit: PAGE_SIZE,
          offset: requestOffset,
          topic: effectiveTopic ?? null,
          forceRemote: reset || forceRemote
        });

        setProblems(prev => (reset ? result.problems : [...prev, ...result.problems]));
        setProblemsTotal(result.total);
        setProblemsOffset(result.nextOffset ?? (requestOffset + result.problems.length));
        setProblemsHasMore(result.hasMore);
      } catch (error) {
        console.error('Failed to load problems:', error);
        if (reset) {
          setProblems([]);
          setProblemsTotal(0);
          setProblemsHasMore(false);
        }
      } finally {
        if (reset) {
          setProblemsLoading(false);
        } else {
          setProblemsLoadingMore(false);
        }
      }
    },
    [company, selectedTopicFilter]
  );

  useEffect(() => {
    loadProblemsRef.current = loadProblems;
  }, [loadProblems]);

  useEffect(() => {
    if (company) {
      setSelectedTopicFilter(null);
      setProblems([]);
      setProblemsTotal(0);
      setProblemsOffset(0);
      setProblemsHasMore(false);
      problemsOffsetRef.current = 0;
      loadProblemsRef.current?.({ reset: true, topic: null, forceRemote: true });
    } else {
      setProblems([]);
      setProblemsTotal(0);
      setProblemsOffset(0);
      setProblemsHasMore(false);
      problemsOffsetRef.current = 0;
    }
  }, [company]);

  const handleTopicToggle = (topic: string) => {
    const nextTopic = selectedTopicFilter === topic ? null : topic;
    setSelectedTopicFilter(nextTopic);
    problemsOffsetRef.current = 0;
    loadProblems({ reset: true, topic: nextTopic });
  };

  const handleProblemSelect = (problem: ProblemData) => {
    setSelectedProblem(problem);
    setPreviewOpen(true);
  };

  const handlePreviewClose = () => {
    setPreviewOpen(false);
    setSelectedProblem(null);
  };
  // Loading state
  if (loading) {
    return (
      <Box>
        <Button
          startIcon={<ArrowBackIcon />}
          onClick={onBack}
          sx={{ mb: 3 }}
        >
          Back to Companies
        </Button>
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}>
          <LoadingSpinner message="Loading company details..." size={60} />
        </Box>
      </Box>
    );
  }

  // Error state
  if (error) {
    return (
      <Box>
        <Button
          startIcon={<ArrowBackIcon />}
          onClick={onBack}
          sx={{ mb: 3 }}
        >
          Back to Companies
        </Button>
        <ErrorMessage
          title="Failed to Load Company Details"
          message={error}
          onRetry={onRetry}
          variant="card"
        />
      </Box>
    );
  }

  // No company data
  if (!company) {
    return (
      <Box>
        <Button
          startIcon={<ArrowBackIcon />}
          onClick={onBack}
          sx={{ mb: 3 }}
        >
          Back to Companies
        </Button>
        <Paper sx={{ p: 6, textAlign: 'center' }}>
          <Typography variant="h6" color="text.secondary">
            Company not found
          </Typography>
        </Paper>
      </Box>
    );
  }

  return (
    <Box>
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 4 }}>
        <Button
          startIcon={<ArrowBackIcon />}
          onClick={onBack}
          variant="outlined"
        >
          Back to Companies
        </Button>
      </Box>

      <Card>
        <CardContent>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 2, flexWrap: 'wrap', mb: 2 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
              <BusinessIcon sx={{ fontSize: 32, color: 'primary.main' }} />
              <Typography variant="h5" sx={{ fontWeight: 600 }}>
                {company.company}
              </Typography>
              {company.rank && (
                <Chip
                  label={`Rank #${company.rank}`}
                  color="primary"
                  variant="outlined"
                  size="small"
                />
              )}
            </Box>
            {problemsLoading && <LoadingSpinner size={20} />}
          </Box>

          {company.topTopics && company.topTopics.length > 0 && (
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mb: 2 }}>
              {company.topTopics.map((topic, index) => {
                const isSelected = selectedTopicFilter === topic;
                const highlightColor = index < 3 ? 'primary' : 'default';
                return (
                  <Chip
                    key={topic}
                    label={topic}
                    size="small"
                    clickable
                    onClick={() => handleTopicToggle(topic)}
                    color={isSelected ? 'primary' : highlightColor}
                    variant={isSelected ? 'filled' : 'outlined'}
                  />
                );
              })}
              {selectedTopicFilter && (
                <Chip
                  label="Clear"
                  size="small"
                  onClick={() => handleTopicToggle(selectedTopicFilter)}
                  variant="outlined"
                  color="secondary"
                />
              )}
            </Box>
          )}

          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            {selectedTopicFilter
              ? `Showing ${problems.length} of ${problemsTotal} problems tagged with "${selectedTopicFilter}"`
              : `Showing ${problems.length} of ${problemsTotal} problems`}
          </Typography>

          {problemsLoading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
              <LoadingSpinner message="Loading problems..." />
            </Box>
          ) : (
            <>
              <ProblemsTable
                problems={problems}
                maxHeight={520}
                onProblemSelect={handleProblemSelect}
              />
              {problemsHasMore && (
                <Box sx={{ display: 'flex', justifyContent: 'center', mt: 2 }}>
                  <Button
                    variant="outlined"
                    onClick={() => loadProblems({ reset: false })}
                    disabled={problemsLoadingMore}
                  >
                    {problemsLoadingMore ? 'Loading…' : 'Load more problems'}
                  </Button>
                </Box>
              )}
            </>
          )}
        </CardContent>
      </Card>

      <ProblemPreviewDrawer
        open={previewOpen}
        problem={selectedProblem}
        onClose={handlePreviewClose}
      />
    </Box>
  );
}
