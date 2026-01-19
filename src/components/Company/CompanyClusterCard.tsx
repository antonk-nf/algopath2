import { useMemo, useState, type ReactElement } from 'react';
import {
  Card,
  CardContent,
  Typography,
  Box,
  Chip,
  Avatar
} from '@mui/material';
import IconButton from '@mui/material/IconButton';
import { algorithms } from '../../data/companyClusters';
import { useIsMobile } from '../../hooks/useIsMobile';

type IconComponent = (props: { size?: number; color?: string }) => ReactElement;

const CLUSTER_ICONS: Record<string, IconComponent> = {
  Building2: ({ size = 18, color = 'currentColor' }) => (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <rect x="3" y="3" width="18" height="18" rx="2" ry="2" />
      <path d="M9 22V12h6v10" />
      <path d="M9 8h6" />
    </svg>
  ),
  ShoppingBag: ({ size = 18, color = 'currentColor' }) => (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <path d="M6 2l.34 3.38A2 2 0 0 0 8.32 7h7.36a2 2 0 0 0 1.98-1.62L18 2" />
      <path d="M3 6h18l-1.5 14.2A2 2 0 0 1 17.52 22H6.48a2 2 0 0 1-1.98-1.8L3 6Z" />
      <path d="M9 10a3 3 0 0 0 6 0" />
    </svg>
  ),
  ChartBar: ({ size = 18, color = 'currentColor' }) => (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <path d="M3 3v18h18" />
      <rect x="7" y="8" width="3" height="9" rx="1" />
      <rect x="12" y="5" width="3" height="12" rx="1" />
      <rect x="17" y="11" width="3" height="6" rx="1" />
    </svg>
  ),
  Briefcase: ({ size = 18, color = 'currentColor' }) => (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <path d="M21 9V7a2 2 0 0 0-2-2h-3V3H8v2H5a2 2 0 0 0-2 2v2" />
      <path d="M3 9h18v8a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2Z" />
      <path d="M10 13h4" />
    </svg>
  ),
  Route: ({ size = 18, color = 'currentColor' }) => (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="6" cy="5" r="2" />
      <circle cx="18" cy="19" r="2" />
      <path d="M6 7v5a6 6 0 0 0 6 6 6 6 0 0 0 6-6v-2" />
    </svg>
  )
};

export function CompanyClusterCard() {
  const clusters = algorithms.B.clusters;
  const totalCompanies = useMemo(
    () => clusters.reduce((sum, cluster) => sum + cluster.companies.length, 0),
    [clusters]
  );
  const isMobile = useIsMobile(960);
  const [currentIndex, setCurrentIndex] = useState(0);

  const advance = (direction: -1 | 1) => {
    setCurrentIndex((prev) => {
      const next = prev + direction;
      if (next < 0) return clusters.length - 1;
      if (next >= clusters.length) return 0;
      return next;
    });
  };

  const displayedClusters = isMobile ? [clusters[currentIndex]] : clusters;

  const clusterCards = displayedClusters.map((cluster) => {
    const Icon = CLUSTER_ICONS[cluster.icon];
    if (!Icon) return null;

    const share = ((cluster.companies.length / totalCompanies) * 100).toFixed(1);
    const topCompanies = cluster.companies.slice(0, 6);
    const remaining = cluster.companies.length - topCompanies.length;

    return (
      <Box
        key={cluster.id}
        sx={{
          border: '1px solid',
          borderColor: 'divider',
          borderRadius: 2,
          p: 2.5,
          display: 'flex',
          flexDirection: 'column',
          gap: 2
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
          <Avatar
            variant="rounded"
            sx={{
              width: 40,
              height: 40,
              bgcolor: `${cluster.color}1a`,
              color: cluster.color
            }}
          >
            <Icon size={20} color={cluster.color} />
          </Avatar>
          <Box>
            <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
              {cluster.label}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              {cluster.companies.length} companies • {share}% of dataset
            </Typography>
          </Box>
        </Box>

        <Typography variant="body2" color="text.secondary">
          {cluster.description}
        </Typography>

        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.75 }}>
          {topCompanies.map((company) => (
            <Chip key={company} label={company} size="small" variant="outlined" />
          ))}
          {remaining > 0 && (
            <Chip
              label={`+${remaining} more`}
              size="small"
              variant="outlined"
              sx={{ borderStyle: 'dashed', color: 'text.secondary' }}
            />
          )}
        </Box>
      </Box>
    );
  });

  return (
    <Card sx={{ borderRadius: 3 }}>
      <CardContent sx={{ p: { xs: 3, md: 4 } }}>
        <Typography variant="h6" component="h2" gutterBottom>
          Company Archetypes
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
          How interview-heavy companies cluster based on shared product focus and hiring style.
        </Typography>

        <Box
          sx={{
            display: 'grid',
            gap: 3,
            gridTemplateColumns: isMobile
              ? '1fr'
              : { xs: 'repeat(2, minmax(0, 1fr))', md: 'repeat(3, minmax(0, 1fr))' }
          }}
        >
          {clusterCards}
        </Box>

        {isMobile && clusters.length > 1 && (
          <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 2 }}>
            <IconButton
              aria-label="previous cluster"
              onClick={() => advance(-1)}
              sx={{ border: '1px solid', borderColor: 'divider' }}
            >
              ‹
            </IconButton>
            <Typography variant="caption" color="text.secondary">
              {currentIndex + 1} / {clusters.length}
            </Typography>
            <IconButton
              aria-label="next cluster"
              onClick={() => advance(1)}
              sx={{ border: '1px solid', borderColor: 'divider' }}
            >
              ›
            </IconButton>
          </Box>
        )}
      </CardContent>
    </Card>
  );
}
