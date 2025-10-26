import React, { useState, useEffect, useMemo } from 'react';
import {
  Typography,
  Box,
  Card,
  CardContent,
  Tabs,
  Tab,
  Alert,
  CircularProgress,
  Chip,
  Button,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Paper,
  IconButton,
  Tooltip
} from '@mui/material';
import {
  Explore as ExploreIcon,
  Diamond as DiamondIcon,
  Star as StarIcon,
  EmojiEvents as TrophyIcon,
  Warning as WarningIcon,
  TrendingUp as TrendingUpIcon,
  FilterList as FilterIcon,
  Share as ShareIcon,
  Refresh as RefreshIcon
} from '@mui/icons-material';
// Using URL search params for shareable links
import { QualityProblemsList } from '../components/Common/QualityProblemsList';
import { HiddenGemsFinder } from '../components/Analytics/HiddenGemsFinder';
import { QualityRecommendationsWidget } from '../components/Analytics/QualityRecommendationsWidget';
import { SentimentHeatmapChart } from '../components/Charts/SentimentHeatmapChart';
import { ExportMenu } from '../components/Common/ExportMenu';
import { companyService } from '../services/companyService';
// import { analyticsService } from '../services/analyticsService';
import type { ProblemData, CompanyData } from '../types';
import type { SentimentHeatmapData } from '../types/analytics';
import { PageContainer } from '../components/Layout';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`discovery-tabpanel-${index}`}
      aria-labelledby={`discovery-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ py: 3 }}>{children}</Box>}
    </div>
  );
}

const DISCOVERY_CATEGORIES = [
  {
    id: 'hidden-gems',
    label: 'Hidden Gems',
    icon: <DiamondIcon />,
    color: '#4CAF50',
    description: 'High-quality problems with low exposure - perfect for standing out'
  },
  {
    id: 'rising-stars',
    label: 'Rising Stars',
    icon: <StarIcon />,
    color: '#2196F3',
    description: 'Problems gaining popularity with strong community engagement'
  },
  {
    id: 'interview-classics',
    label: 'Interview Classics',
    icon: <TrophyIcon />,
    color: '#FF9800',
    description: 'Time-tested problems frequently asked in interviews'
  },
  {
    id: 'controversial',
    label: 'Controversial',
    icon: <WarningIcon />,
    color: '#F44336',
    description: 'Problems with mixed community reception - approach with caution'
  }
];

export const DiscoveryPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState(() => {
    const urlParams = new URLSearchParams(window.location.search);
    const tab = urlParams.get('tab');
    return tab ? parseInt(tab, 10) : 0;
  });
  
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [problems, setProblems] = useState<ProblemData[]>([]);
  const [, setCompanies] = useState<CompanyData[]>([]);
  const [sentimentData, setSentimentData] = useState<SentimentHeatmapData[]>([]);
  
  // Filters
  const [selectedCompanies, setSelectedCompanies] = useState<string[]>([]);
  const [selectedDifficulties, setSelectedDifficulties] = useState<string[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<string>('all');

  const handleTabChange = (_event: React.SyntheticEvent, newValue: number) => {
    setActiveTab(newValue);
    // Update URL for shareable links
    const url = new URL(window.location.href);
    url.searchParams.set('tab', newValue.toString());
    window.history.replaceState({}, '', url.toString());
  };

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);

      // Load problems and companies data
      const [companiesData] = await Promise.all([
        companyService.getCompanyStats()
      ]);

      setCompanies(companiesData);

      // For now, we'll use mock data since the company service doesn't include individual problems
      // In a real implementation, you'd fetch from a problems endpoint
      const mockProblems: ProblemData[] = [
        {
          title: "Two Sum",
          difficulty: "EASY" as const,
          topics: ["Array", "Hash Table"],
          company: "Google",
          frequency: 8.5,
          acceptanceRate: 0.49,
          likes: 15234,
          dislikes: 892,
          originalityScore: 0.94,
          totalVotes: 16126,
          qualityTier: "interview-classic",
          link: "https://leetcode.com/problems/two-sum/"
        },
        {
          title: "Valid Parentheses",
          difficulty: "EASY" as const,
          topics: ["String", "Stack"],
          company: "Amazon",
          frequency: 7.2,
          acceptanceRate: 0.40,
          likes: 8934,
          dislikes: 423,
          originalityScore: 0.95,
          totalVotes: 9357,
          qualityTier: "interview-classic",
          link: "https://leetcode.com/problems/valid-parentheses/"
        }
        // Add more mock problems as needed
      ];

      setProblems(mockProblems);

      // Generate sentiment heatmap data
      const sentimentMap = new Map<string, { likes: number; dislikes: number; count: number }>();
      
      mockProblems.forEach(problem => {
        if (problem.likes && problem.dislikes) {
          const key = `${problem.topics[0] || 'Other'}-${problem.difficulty}`;
          const existing = sentimentMap.get(key) || { likes: 0, dislikes: 0, count: 0 };
          sentimentMap.set(key, {
            likes: existing.likes + problem.likes,
            dislikes: existing.dislikes + problem.dislikes,
            count: existing.count + 1
          });
        }
      });

      const sentimentHeatmap: SentimentHeatmapData[] = Array.from(sentimentMap.entries()).map(([key, data]) => {
        const [topic, difficulty] = key.split('-');
        const totalVotes = data.likes + data.dislikes;
        const sentimentRatio = totalVotes > 0 ? data.likes / totalVotes : 0.5;
        
        let sentiment: 'positive' | 'neutral' | 'negative';
        if (sentimentRatio > 0.7) {
          sentiment = 'positive';
        } else if (sentimentRatio < 0.4) {
          sentiment = 'negative';
        } else {
          sentiment = 'neutral';
        }
        
        return {
          topic,
          difficulty: difficulty as 'EASY' | 'MEDIUM' | 'HARD',
          sentiment,
          problemCount: data.count,
          avgLikes: data.likes / data.count,
          avgDislikes: data.dislikes / data.count,
          avgOriginalityScore: 0.8 // Mock value
        };
      });

      setSentimentData(sentimentHeatmap);

    } catch (err) {
      console.error('Failed to load discovery data:', err);
      setError('Failed to load discovery data. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = () => {
    loadData();
  };

  const handleShareCategory = (categoryId: string) => {
    const url = new URL(window.location.href);
    url.searchParams.set('category', categoryId);
    url.searchParams.set('tab', activeTab.toString());
    
    navigator.clipboard.writeText(url.toString()).then(() => {
      // Could show a toast notification here
      console.log('Link copied to clipboard');
    });
  };

  // Filter problems based on selected criteria
  const filteredProblems = useMemo(() => {
    return problems.filter(problem => {
      if (selectedCompanies.length > 0 && !selectedCompanies.includes(problem.company)) {
        return false;
      }
      if (selectedDifficulties.length > 0 && !selectedDifficulties.includes(problem.difficulty)) {
        return false;
      }
      return true;
    });
  }, [problems, selectedCompanies, selectedDifficulties]);

  // Categorize problems by quality tiers
  const categorizedProblems = useMemo(() => {
    const categories = {
      'hidden-gems': [] as ProblemData[],
      'rising-stars': [] as ProblemData[],
      'interview-classics': [] as ProblemData[],
      'controversial': [] as ProblemData[]
    };

    filteredProblems.forEach(problem => {
      if (!problem.originalityScore || !problem.totalVotes || !problem.likes) {
        return;
      }

      const { originalityScore, totalVotes, likes } = problem;

      if (originalityScore > 0.85 && totalVotes < 1000 && likes > 50) {
        categories['hidden-gems'].push(problem);
      } else if (originalityScore > 0.8 && totalVotes >= 1000 && totalVotes <= 5000 && likes > 100) {
        categories['rising-stars'].push(problem);
      } else if (likes > 1000 && totalVotes > 5000) {
        categories['interview-classics'].push(problem);
      } else if (originalityScore < 0.7) {
        categories['controversial'].push(problem);
      }
    });

    return categories;
  }, [filteredProblems]);

  useEffect(() => {
    loadData();
  }, []);

  if (loading) {
    return (
      <PageContainer sx={{ py: 4 }}>
        <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
          <CircularProgress size={60} />
        </Box>
      </PageContainer>
    );
  }

  return (
    <PageContainer sx={{ py: 4 }}>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={4}>
        <Box>
          <Typography variant="h4" component="h1" gutterBottom>
            <ExploreIcon sx={{ mr: 2, verticalAlign: 'middle' }} />
            Problem Discovery
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Discover high-quality problems curated by community sentiment and engagement metrics
          </Typography>
        </Box>
        <Box display="flex" gap={1}>
          <ExportMenu
            data={filteredProblems}
            dataType="problems"
            buttonText="Export Problems"
            disabled={filteredProblems.length === 0}
          />
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={handleRefresh}
            disabled={loading}
          >
            Refresh
          </Button>
        </Box>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {/* Quick Stats */}
      <Box sx={{ 
        display: 'grid', 
        gridTemplateColumns: { xs: '1fr', sm: '1fr 1fr', md: '1fr 1fr 1fr 1fr' }, 
        gap: 3, 
        mb: 4 
      }}>
        {DISCOVERY_CATEGORIES.map((category) => {
          const count = categorizedProblems[category.id as keyof typeof categorizedProblems].length;
          return (
            <Card 
              key={category.id}
              sx={{ 
                cursor: 'pointer',
                transition: 'all 0.2s',
                '&:hover': { 
                  transform: 'translateY(-2px)',
                  boxShadow: 3
                }
              }}
              onClick={() => {
                setSelectedCategory(category.id);
                setActiveTab(1); // Switch to filtered view
              }}
            >
              <CardContent sx={{ textAlign: 'center' }}>
                <Box sx={{ color: category.color, mb: 1 }}>
                  {React.cloneElement(category.icon, { fontSize: 'large' })}
                </Box>
                <Typography variant="h4" sx={{ color: category.color, fontWeight: 'bold' }}>
                  {count}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {category.label}
                </Typography>
              </CardContent>
            </Card>
          );
        })}
      </Box>

      {/* Tabs */}
      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
        <Tabs value={activeTab} onChange={handleTabChange} aria-label="discovery tabs">
          <Tab 
            icon={<TrendingUpIcon />} 
            label="Overview" 
            id="discovery-tab-0"
          />
          <Tab 
            icon={<FilterIcon />} 
            label="Curated Lists" 
            id="discovery-tab-1"
          />
          <Tab 
            icon={<DiamondIcon />} 
            label="Hidden Gems Finder" 
            id="discovery-tab-2"
          />
          <Tab 
            icon={<StarIcon />} 
            label="Quality Recommendations" 
            id="discovery-tab-3"
          />
        </Tabs>
      </Box>

      {/* Overview Tab */}
      <TabPanel value={activeTab} index={0}>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
          {/* Community Sentiment Heatmap */}
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Community Sentiment Analysis
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                Sentiment trends across topics and difficulty levels based on community likes/dislikes
              </Typography>
              <SentimentHeatmapChart 
                data={sentimentData}
                height={400}
              />
            </CardContent>
          </Card>

          {/* Category Overview */}
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Discovery Categories
              </Typography>
              <Box sx={{ 
                display: 'grid', 
                gridTemplateColumns: { xs: '1fr', md: '1fr 1fr' }, 
                gap: 2 
              }}>
                {DISCOVERY_CATEGORIES.map((category) => {
                  const count = categorizedProblems[category.id as keyof typeof categorizedProblems].length;
                  return (
                    <Paper key={category.id} sx={{ p: 2, display: 'flex', alignItems: 'center', gap: 2 }}>
                      <Box sx={{ color: category.color }}>
                        {category.icon}
                      </Box>
                      <Box sx={{ flex: 1 }}>
                        <Typography variant="subtitle1" sx={{ fontWeight: 'medium' }}>
                          {category.label} ({count})
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          {category.description}
                        </Typography>
                      </Box>
                      <Tooltip title="Share category">
                        <IconButton 
                          size="small"
                          onClick={() => handleShareCategory(category.id)}
                        >
                          <ShareIcon />
                        </IconButton>
                      </Tooltip>
                    </Paper>
                  );
                })}
              </Box>
            </CardContent>
          </Card>
        </Box>
      </TabPanel>

      {/* Curated Lists Tab */}
      <TabPanel value={activeTab} index={1}>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
          {/* Filters */}
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Filter Problems
              </Typography>
              <Box display="flex" gap={2} flexWrap="wrap" alignItems="center">
                <FormControl sx={{ minWidth: 200 }}>
                  <InputLabel>Category</InputLabel>
                  <Select
                    value={selectedCategory}
                    onChange={(e) => setSelectedCategory(e.target.value)}
                    label="Category"
                  >
                    <MenuItem value="all">All Categories</MenuItem>
                    {DISCOVERY_CATEGORIES.map((category) => (
                      <MenuItem key={category.id} value={category.id}>
                        {category.label}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
                
                <FormControl sx={{ minWidth: 200 }}>
                  <InputLabel>Companies</InputLabel>
                  <Select
                    multiple
                    value={selectedCompanies}
                    onChange={(e) => setSelectedCompanies(typeof e.target.value === 'string' ? [e.target.value] : e.target.value)}
                    label="Companies"
                    renderValue={(selected) => (
                      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                        {selected.map((value) => (
                          <Chip key={value} label={value} size="small" />
                        ))}
                      </Box>
                    )}
                  >
                    {Array.from(new Set(problems.map(p => p.company))).sort().map((company) => (
                      <MenuItem key={company} value={company}>
                        {company}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>

                <FormControl sx={{ minWidth: 200 }}>
                  <InputLabel>Difficulty</InputLabel>
                  <Select
                    multiple
                    value={selectedDifficulties}
                    onChange={(e) => setSelectedDifficulties(typeof e.target.value === 'string' ? [e.target.value] : e.target.value)}
                    label="Difficulty"
                    renderValue={(selected) => (
                      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                        {selected.map((value) => (
                          <Chip key={value} label={value} size="small" />
                        ))}
                      </Box>
                    )}
                  >
                    {['EASY', 'MEDIUM', 'HARD'].map((difficulty) => (
                      <MenuItem key={difficulty} value={difficulty}>
                        {difficulty}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Box>
            </CardContent>
          </Card>

          {/* Filtered Problems List */}
          {selectedCategory === 'all' ? (
            <QualityProblemsList
              problems={filteredProblems}
              title="All Quality Problems"
              showFilters={false}
              defaultShowQualityMetrics={true}
            />
          ) : (
            <QualityProblemsList
              problems={categorizedProblems[selectedCategory as keyof typeof categorizedProblems]}
              title={`${DISCOVERY_CATEGORIES.find(c => c.id === selectedCategory)?.label} Problems`}
              showFilters={false}
              defaultShowQualityMetrics={true}
            />
          )}
        </Box>
      </TabPanel>

      {/* Hidden Gems Finder Tab */}
      <TabPanel value={activeTab} index={2}>
        <HiddenGemsFinder problems={filteredProblems} />
      </TabPanel>

      {/* Quality Recommendations Tab */}
      <TabPanel value={activeTab} index={3}>
        <QualityRecommendationsWidget 
          problems={filteredProblems}
          userSkillLevel="intermediate"
        />
      </TabPanel>
    </PageContainer>
  );
};
