import { useState, useEffect, useRef } from 'react';
import {
  Box,
  Typography,
  Alert,
  Snackbar,
  CircularProgress,
  Backdrop,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions
} from '@mui/material';
import {
  Upload as UploadIcon
} from '@mui/icons-material';
import { StudyPlanForm, StudyPlanView, StudyPlanList, StorageInfo } from '../components/StudyPlan';
import { LoadingSpinner } from '../components/Common';
import { ExportService } from '../services/exportService';
import { companyService } from '../services/companyService';
import { studyPlanService } from '../services/studyPlanService';
import { staticDataService } from '../services/staticDataService';
import { apiClient, ApiClientError } from '../services/apiClient';
import type {
  StudyPlan,
  StudyPlanFormData,
  CompanyData,
  ProblemData,
  StudyPlanRecommendationResponse
} from '../types';

// Check if running in static mode (no API server)
const isStaticMode = (): boolean => {
  if (import.meta.env.VITE_STATIC_MODE === 'true') {
    return true;
  }
  if (import.meta.env.PROD) {
    return true;
  }
  return false;
};

type ViewMode = 'list' | 'create' | 'view';

export function StudyPlannerPage() {
  const [viewMode, setViewMode] = useState<ViewMode>('list');
  const [studyPlans, setStudyPlans] = useState<StudyPlan[]>([]);
  const [selectedPlan, setSelectedPlan] = useState<StudyPlan | null>(null);
  const [companies, setCompanies] = useState<CompanyData[]>([]);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [importDialogOpen, setImportDialogOpen] = useState(false);
  const [importing, setImporting] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    loadInitialData();
  }, []);

  const loadInitialData = async () => {
    try {
      setLoading(true);
      
      // Load companies data
      const companiesData = await companyService.getCompanyStats();
      setCompanies(companiesData);
      
      // Load existing study plans
      const existingPlans = studyPlanService.getStudyPlans();
      setStudyPlans(existingPlans);
      
    } catch (error) {
      console.error('Failed to load initial data:', error);
      setError('Failed to load company data. Some features may be limited.');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateStudyPlan = async (formData: StudyPlanFormData) => {
    try {
      setGenerating(true);
      setError(null);

      const durationWeeks = formData.duration;
      const dailyGoal = formData.dailyGoal;
      const focusTopics = formData.focusAreas && formData.focusAreas.length > 0
        ? formData.focusAreas
        : undefined;

      let availableProblems: ProblemData[];
      let requestedTotal = durationWeeks * 7 * dailyGoal;

      if (isStaticMode()) {
        // In static mode, load all problems and filter client-side
        const allProblems = await staticDataService.loadAllProblems();

        // Filter problems by target companies
        let filtered = allProblems.filter(p =>
          p.companies.some(c => formData.targetCompanies.includes(c))
        );

        // Filter by focus topics if specified
        if (focusTopics && focusTopics.length > 0) {
          filtered = filtered.filter(p =>
            p.topics.some(t => focusTopics.some(ft =>
              t.toLowerCase().includes(ft.toLowerCase())
            ))
          );
        }

        // Filter by difficulty based on skill level
        if (formData.skillLevel === 'beginner') {
          filtered = filtered.filter(p => p.difficulty !== 'HARD');
        }

        // Sort by frequency (higher first)
        filtered.sort((a, b) => (b.frequency || 0) - (a.frequency || 0));

        // Convert to ProblemData format
        availableProblems = filtered.slice(0, requestedTotal * 2).map(item => ({
          title: item.title,
          difficulty: (item.difficulty as 'EASY' | 'MEDIUM' | 'HARD' | 'UNKNOWN') || 'UNKNOWN',
          topics: item.topics,
          company: item.companies.find(c => formData.targetCompanies.includes(c)) || item.companies[0] || '',
          link: item.link || undefined,
          frequency: item.frequency,
          acceptanceRate: item.acceptanceRate,
          timeframe: 'custom',
          totalFrequency: item.frequency,
          companyCount: item.companyCount,
        }));
      } else {
        // API mode - existing behavior
        const response = await apiClient.getStudyPlanRecommendations({
          companies: formData.targetCompanies,
          focus_topics: focusTopics,
          skill_level: formData.skillLevel,
          duration_weeks: durationWeeks,
          daily_goal: dailyGoal,
          balance_companies: true,
          max_per_company: undefined,
        });

        const payload = response.data as StudyPlanRecommendationResponse;
        const recommendations = Array.isArray(payload?.recommendations)
          ? payload.recommendations
          : [];

        if (recommendations.length === 0) {
          throw new Error('No suitable problems were returned. Try adjusting your filters.');
        }

        requestedTotal = payload?.requested_count ?? requestedTotal;
        availableProblems = recommendations.map((item) => ({
          title: item.title,
          difficulty: (item.difficulty as 'EASY' | 'MEDIUM' | 'HARD' | 'UNKNOWN') || 'UNKNOWN',
          topics: Array.isArray(item.topics) ? item.topics : [],
          company: item.recommended_company || (Array.isArray(item.companies) ? item.companies[0] : formData.targetCompanies[0] || ''),
          link: item.link || undefined,
          frequency: typeof item.frequency === 'number' ? item.frequency : undefined,
          acceptanceRate: typeof item.acceptance_rate === 'number' ? item.acceptance_rate : undefined,
          timeframe: 'custom',
          totalFrequency: typeof item.frequency === 'number' ? item.frequency : undefined,
          companyCount: Array.isArray(item.companies) ? item.companies.length : undefined,
        }));
      }

      if (availableProblems.length === 0) {
        throw new Error('No suitable problems were found. Try adjusting your filters.');
      }

      const trimmedProblems = availableProblems.slice(0, requestedTotal);
      const actualSelected = trimmedProblems.length;

      const finalProblems = trimmedProblems;

      const effectiveDays = Math.max(1, Math.ceil(actualSelected / Math.max(dailyGoal, 1)));
      const adjustedDurationWeeks = Math.max(1, Math.ceil(effectiveDays / 7));

      const adjustedFormData: StudyPlanFormData = {
        ...formData,
        duration: adjustedDurationWeeks
      };

      const newPlan = studyPlanService.generateStudyPlan(
        adjustedFormData,
        finalProblems,
        companies,
        {
          balanceAcrossCompanies: true,
          maxProblemsPerCompany: 50,
          learningMode: formData.learningMode || 'balanced',
          qualityPreference: formData.qualityPreference || 'balanced',
          adaptiveDifficulty: formData.adaptiveDifficulty ?? true,
          includeQualityMetrics: formData.includeQualityMetrics ?? true,
          minQualityScore: 0.0
        }
      );

      // Save the plan
      studyPlanService.saveStudyPlan(newPlan);

      // Update local state
      setStudyPlans(prev => [...prev, newPlan]);
      setSelectedPlan(newPlan);
      setViewMode('view');

      const messageParts: string[] = [];
      if (actualSelected < requestedTotal) {
        messageParts.push(
          `Study plan created with ${actualSelected} problems (requested ${requestedTotal}).`
        );
        messageParts.push(`Duration adjusted to ${adjustedDurationWeeks} week(s).`);
      } else {
        messageParts.push(`Study plan created with ${actualSelected} problems.`);
      }

      const summaryMessage = messageParts.join(' ');

      setSuccessMessage(summaryMessage);

    } catch (error) {
      console.error('Failed to create study plan:', error);

      if (error instanceof ApiClientError) {
        setError(error.message);
      } else if (error instanceof Error) {
        setError(error.message);
      } else {
        setError('Failed to create study plan. Please try again.');
      }
    } finally {
      setGenerating(false);
    }
  };

  const handleSelectPlan = (plan: StudyPlan) => {
    setSelectedPlan(plan);
    setViewMode('view');
  };

  const handleUpdatePlan = (updatedPlan: StudyPlan) => {
    setStudyPlans(prev => 
      prev.map(plan => plan.id === updatedPlan.id ? updatedPlan : plan)
    );
    setSelectedPlan(updatedPlan);
  };

  const handleDeletePlan = (planId: string) => {
    studyPlanService.deleteStudyPlan(planId);
    setStudyPlans(prev => prev.filter(plan => plan.id !== planId));
    
    if (selectedPlan?.id === planId) {
      setSelectedPlan(null);
      setViewMode('list');
    }
    
    setSuccessMessage('Study plan deleted successfully.');
  };

  const handleBackToList = () => {
    setSelectedPlan(null);
    setViewMode('list');
  };

  const handleCreateNew = () => {
    setSelectedPlan(null);
    setViewMode('create');
  };

  const handleImportClick = () => {
    setImportDialogOpen(true);
  };

  const handleImportFile = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    try {
      setImporting(true);
      const importedPlans = await ExportService.importStudyPlans(file);
      
      // Add imported plans to existing plans
      const existingPlans = studyPlanService.getStudyPlans();
      const newPlans = importedPlans.filter(
        importedPlan => !existingPlans.some(existing => existing.id === importedPlan.id)
      );
      
      newPlans.forEach(plan => {
        studyPlanService.saveStudyPlan(plan);
      });
      
      // Refresh the study plans list
      const updatedPlans = studyPlanService.getStudyPlans();
      setStudyPlans(updatedPlans);
      
      setSuccessMessage(`Successfully imported ${newPlans.length} study plan(s).`);
      setImportDialogOpen(false);
      
      // Reset file input
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    } catch (error) {
      setError(error instanceof Error ? error.message : 'Failed to import study plans');
    } finally {
      setImporting(false);
    }
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}>
        <LoadingSpinner message="Loading study planner..." />
      </Box>
    );
  }

  return (
    <Box>
      {/* Page Header */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          Study Planner
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Create personalized study plans based on your target companies and preparation timeline.
          Track your progress and stay motivated with daily goals and streak tracking.
        </Typography>
      </Box>

      {/* Error Alert */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* Storage Info */}
      {viewMode === 'list' && (
        <Box sx={{ mb: 3 }}>
          <StorageInfo 
            onExport={() => {
              try {
                ExportService.exportMultipleStudyPlans(studyPlans);
              } catch (error) {
                console.error('Export failed:', error);
                setError('Failed to export study plans');
              }
            }}
          />
          <Box sx={{ mt: 2, display: 'flex', gap: 2 }}>
            <Button
              variant="outlined"
              startIcon={<UploadIcon />}
              onClick={handleImportClick}
            >
              Import Study Plans
            </Button>
          </Box>
        </Box>
      )}

      {/* Main Content */}
      {viewMode === 'list' && (
        <StudyPlanList
          studyPlans={studyPlans}
          onSelect={handleSelectPlan}
          onDelete={handleDeletePlan}
          onCreateNew={handleCreateNew}
          onRefresh={() => {
            const existingPlans = studyPlanService.getStudyPlans();
            setStudyPlans(existingPlans);
          }}
        />
      )}

      {viewMode === 'create' && (
        <Box>
          <Box sx={{ mb: 3 }}>
            <Typography variant="h5" gutterBottom>
              Create New Study Plan
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Fill out the form below to generate a personalized study plan.
            </Typography>
          </Box>
          
          <StudyPlanForm
            companies={companies}
            onSubmit={handleCreateStudyPlan}
            loading={generating}
          />
          
          <Box sx={{ mt: 2 }}>
            <Typography 
              variant="body2" 
              color="primary" 
              sx={{ cursor: 'pointer', textDecoration: 'underline' }}
              onClick={handleBackToList}
            >
              ← Back to Study Plans
            </Typography>
          </Box>
        </Box>
      )}

      {viewMode === 'view' && selectedPlan && (
        <Box>
          <Box sx={{ mb: 3 }}>
            <Typography 
              variant="body2" 
              color="primary" 
              sx={{ cursor: 'pointer', textDecoration: 'underline' }}
              onClick={handleBackToList}
            >
              ← Back to Study Plans
            </Typography>
          </Box>
          
          <StudyPlanView
            studyPlan={selectedPlan}
            onUpdate={handleUpdatePlan}
            onDelete={handleDeletePlan}
          />
        </Box>
      )}

      {/* Loading Backdrop */}
      <Backdrop
        sx={{ color: '#fff', zIndex: (theme) => theme.zIndex.drawer + 1 }}
        open={generating}
      >
        <Box sx={{ textAlign: 'center' }}>
          <CircularProgress color="inherit" />
          <Typography variant="h6" sx={{ mt: 2 }}>
            Generating Study Plan...
          </Typography>
          <Typography variant="body2" sx={{ mt: 1 }}>
            This may take a few moments
          </Typography>
        </Box>
      </Backdrop>

      {/* Import Dialog */}
      <Dialog open={importDialogOpen} onClose={() => setImportDialogOpen(false)}>
        <DialogTitle>Import Study Plans</DialogTitle>
        <DialogContent>
          <Typography variant="body2" sx={{ mb: 2 }}>
            Select a JSON file containing exported study plans to import them into your collection.
          </Typography>
          <input
            type="file"
            accept=".json"
            onChange={handleFileChange}
            ref={fileInputRef}
            style={{ display: 'none' }}
          />
          <Button
            variant="outlined"
            onClick={handleImportFile}
            disabled={importing}
            fullWidth
          >
            {importing ? 'Importing...' : 'Choose File'}
          </Button>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setImportDialogOpen(false)} disabled={importing}>
            Cancel
          </Button>
        </DialogActions>
      </Dialog>

      {/* Success Snackbar */}
      <Snackbar
        open={!!successMessage}
        autoHideDuration={4000}
        onClose={() => setSuccessMessage(null)}
        message={successMessage}
      />
    </Box>
  );
}
