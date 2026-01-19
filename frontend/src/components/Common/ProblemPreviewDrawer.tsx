import React, { useEffect, useMemo, useState } from 'react';
import {
  Drawer,
  Box,
  Typography,
  IconButton,
  Chip,
  Stack,
  Divider,
  CircularProgress,
  Alert,
  Tooltip,
  Link as MuiLink
} from '@mui/material';
import CloseIcon from '@mui/icons-material/Close';
import OpenInNewIcon from '@mui/icons-material/OpenInNew';
import ThumbUpIcon from '@mui/icons-material/ThumbUp';
import ThumbDownIcon from '@mui/icons-material/ThumbDown';
import LocalLibraryIcon from '@mui/icons-material/LocalLibrary';
import VideoLibraryIcon from '@mui/icons-material/VideoLibrary';
import LockIcon from '@mui/icons-material/Lock';

import type { ProblemData, ProblemPreview } from '../../types';
import { fetchProblemPreview } from '../../services/problemService';
import { ApiClientError } from '../../services/apiClient';

interface ProblemPreviewDrawerProps {
  open: boolean;
  problem: ProblemData | null;
  onClose: () => void;
}

const getProblemSlug = (problem: ProblemData | null): string | null => {
  if (!problem) {
    return null;
  }

  if (problem.titleSlug) {
    return problem.titleSlug;
  }

  if (problem.link) {
    const match = problem.link.match(/leetcode\.com\/problems\/([\w-]+)/i);
    if (match) {
      return match[1].toLowerCase();
    }
  }

  return null;
};

const formatAcceptance = (value?: number | null): string => {
  if (typeof value !== 'number' || Number.isNaN(value)) {
    return '—';
  }
  return `${value.toFixed(1)}%`;
};

export const ProblemPreviewDrawer: React.FC<ProblemPreviewDrawerProps> = ({
  open,
  problem,
  onClose
}) => {
  const slug = useMemo(() => getProblemSlug(problem), [problem]);
  const [preview, setPreview] = useState<ProblemPreview | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!open) {
      return;
    }

    if (!slug) {
      setPreview(null);
      setError('Unable to load preview – missing problem identifier.');
      return;
    }

    let cancelled = false;
    setLoading(true);
    setError(null);
    setPreview(null);

    fetchProblemPreview(slug, {
      acceptanceRate: problem?.acceptanceRate,
      topics: problem?.topics
    })
      .then((data) => {
        if (!cancelled) {
          setPreview(data);
        }
      })
      .catch((err) => {
        if (cancelled) {
          return;
        }
        if (err instanceof ApiClientError) {
          setError(err.message || 'Failed to load problem preview.');
        } else if (err instanceof Error) {
          setError(err.message);
        } else {
          setError('Failed to load problem preview.');
        }
      })
      .finally(() => {
        if (!cancelled) {
          setLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [open, slug, problem]);

  useEffect(() => {
    if (!open) {
      setPreview(null);
      setError(null);
      setLoading(false);
    }
  }, [open]);

  const renderTopicChips = () => {
    if (!preview?.topic_tags || preview.topic_tags.length === 0) {
      return null;
    }

    return (
      <Stack direction="row" spacing={0.5} flexWrap="wrap" sx={{ mt: 1 }}>
        {preview.topic_tags.map((tag) => (
          <Chip
            key={tag.slug || tag.name}
            label={tag.name}
            size="small"
            variant="outlined"
          />
        ))}
      </Stack>
    );
  };

  const renderMetadata = () => {
    if (!preview) {
      return null;
    }

    return (
      <Stack direction="row" spacing={2} flexWrap="wrap" sx={{ mt: 2 }}>
        {typeof preview.likes === 'number' && (
          <Stack direction="row" spacing={0.5} alignItems="center">
            <ThumbUpIcon fontSize="small" color="success" />
            <Typography variant="body2">{preview.likes.toLocaleString()}</Typography>
          </Stack>
        )}
        {typeof preview.dislikes === 'number' && preview.dislikes > 0 && (
          <Stack direction="row" spacing={0.5} alignItems="center">
            <ThumbDownIcon fontSize="small" color="error" />
            <Typography variant="body2">{preview.dislikes.toLocaleString()}</Typography>
          </Stack>
        )}
        {typeof preview.ac_rate === 'number' && (
          <Typography variant="body2" color="text.secondary">
            Acceptance: {formatAcceptance(preview.ac_rate)}
          </Typography>
        )}
        {preview.has_solution && (
          <Stack direction="row" spacing={0.5} alignItems="center">
            <LocalLibraryIcon fontSize="small" color="primary" />
            <Typography variant="body2">Solution Available</Typography>
          </Stack>
        )}
        {preview.has_video_solution && (
          <Stack direction="row" spacing={0.5} alignItems="center">
            <VideoLibraryIcon fontSize="small" color="primary" />
            <Typography variant="body2">Video Solution</Typography>
          </Stack>
        )}
        {preview.is_paid_only && (
          <Stack direction="row" spacing={0.5} alignItems="center">
            <LockIcon fontSize="small" color="warning" />
            <Typography variant="body2">Paid Only</Typography>
          </Stack>
        )}
      </Stack>
    );
  };

  return (
    <Drawer
      anchor="right"
      open={open}
      onClose={onClose}
      PaperProps={{
        sx: {
          width: { xs: '100%', sm: 520 },
          maxWidth: '100%',
          display: 'flex',
          flexDirection: 'column'
        }
      }}
    >
      <Box
        sx={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          p: 2,
          borderBottom: '1px solid',
          borderColor: 'divider'
        }}
      >
        <Box>
          <Typography variant="h6" sx={{ mb: 0.5 }}>
            {problem?.title || 'Problem Preview'}
          </Typography>
          {problem?.company && (
            <Typography variant="body2" color="text.secondary">
              {problem.company}
            </Typography>
          )}
        </Box>
        <Box>
          {problem?.link && (
            <Tooltip title="Open in LeetCode">
              <IconButton
                component={MuiLink}
                href={problem.link}
                target="_blank"
                rel="noopener noreferrer"
                size="small"
                sx={{ mr: 1 }}
                onClick={(event) => event.stopPropagation()}
              >
                <OpenInNewIcon fontSize="small" />
              </IconButton>
            </Tooltip>
          )}
          <IconButton onClick={onClose} size="small">
            <CloseIcon />
          </IconButton>
        </Box>
      </Box>

      <Box sx={{ p: 2, overflowY: 'auto', flexGrow: 1 }}>
        {problem?.difficulty && (
          <Chip
            label={problem.difficulty}
            size="small"
            color={
              problem.difficulty === 'EASY'
                ? 'success'
                : problem.difficulty === 'MEDIUM'
                ? 'warning'
                : 'error'
            }
            sx={{ mb: 1 }}
          />
        )}

        {renderTopicChips()}
        {renderMetadata()}

        <Divider sx={{ my: 2 }} />

        {loading && (
          <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
            <CircularProgress size={28} />
          </Box>
        )}

        {!loading && error && (
          <Alert severity="error" sx={{ mt: 2 }}>
            {error}
          </Alert>
        )}

        {!loading && !error && preview && (
          (() => {
            const html = preview.content_html?.trim();
            const text = preview.content_text?.trim();

            if (html) {
              return (
                <Box
                  sx={{
                    '& h1, & h2, & h3, & h4, & h5, & h6': { mt: 2, mb: 1 },
                    '& p': { lineHeight: 1.6 },
                    '& pre': {
                      p: 1.5,
                      bgcolor: 'grey.100',
                      borderRadius: 1,
                      overflowX: 'auto'
                    },
                    '& img': {
                      maxWidth: '100%',
                      borderRadius: 1,
                      my: 1
                    },
                    '& ul, & ol': {
                      pl: 3,
                      mb: 2
                    }
                  }}
                  dangerouslySetInnerHTML={{ __html: html }}
                />
              );
            }

            if (text) {
              return (
                <Typography
                  variant="body2"
                  sx={{ whiteSpace: 'pre-line', lineHeight: 1.6 }}
                >
                  {text}
                </Typography>
              );
            }

            return (
              <Alert severity="info">
                Preview unavailable for this problem.{' '}
                {problem?.link ? (
                  <MuiLink
                    href={problem.link}
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    Open on LeetCode
                  </MuiLink>
                ) : (
                  'Try opening directly on LeetCode.'
                )}
              </Alert>
            );
          })()
        )}
      </Box>
    </Drawer>
  );
};
