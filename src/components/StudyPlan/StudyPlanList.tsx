import { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Chip,
  LinearProgress,
  Stack,
  IconButton,
  Alert,
  Menu,
  MenuItem,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField
} from '@mui/material';
import {
  Delete as DeleteIcon,
  PlayArrow as PlayArrowIcon,
  MoreVert as MoreVertIcon,
  Download as DownloadIcon,
  Upload as UploadIcon,
  Warning as WarningIcon
} from '@mui/icons-material';
import type { StudyPlan } from '../../types';
import { studyPlanService } from '../../services/studyPlanService';

interface StudyPlanListProps {
  studyPlans: StudyPlan[];
  onSelect: (studyPlan: StudyPlan) => void;
  onDelete: (planId: string) => void;
  onCreateNew: () => void;
  onRefresh: () => void;
}

export function StudyPlanList({ studyPlans, onSelect, onDelete, onCreateNew, onRefresh }: StudyPlanListProps) {
  const [menuAnchor, setMenuAnchor] = useState<null | HTMLElement>(null);
  const [importDialog, setImportDialog] = useState(false);
  const [importData, setImportData] = useState('');
  const [storageWarning, setStorageWarning] = useState<string | null>(null);

  // Check storage on component mount
  useState(() => {
    const storageInfo = studyPlanService.getStorageInfo();
    if (storageInfo.percentage > 80) {
      setStorageWarning(`Storage is ${storageInfo.percentage}% full (${storageInfo.used}KB used). Consider exporting your data.`);
    }
  });
  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    });
  };

  const getTimeRemaining = (studyPlan: StudyPlan) => {
    const startDate = new Date(studyPlan.schedule[0]?.date || studyPlan.createdAt);
    const endDate = new Date(startDate);
    endDate.setDate(startDate.getDate() + (studyPlan.duration * 7));
    
    const today = new Date();
    const daysRemaining = Math.ceil((endDate.getTime() - today.getTime()) / (1000 * 60 * 60 * 24));
    
    if (daysRemaining < 0) {
      return { status: 'completed', text: 'Completed' };
    } else if (daysRemaining === 0) {
      return { status: 'today', text: 'Last day!' };
    } else if (daysRemaining <= 7) {
      return { status: 'ending', text: `${daysRemaining} days left` };
    } else {
      const weeksRemaining = Math.ceil(daysRemaining / 7);
      return { status: 'active', text: `${weeksRemaining} weeks left` };
    }
  };

  const handleExport = () => {
    try {
      const exportData = studyPlanService.exportStudyPlans();
      const blob = new Blob([exportData], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `study-plans-${new Date().toISOString().split('T')[0]}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      setMenuAnchor(null);
    } catch (error) {
      console.error('Export failed:', error);
    }
  };

  const handleImport = () => {
    try {
      const result = studyPlanService.importStudyPlans(importData);
      if (result.success) {
        onRefresh();
        setImportDialog(false);
        setImportData('');
        alert(result.message);
      } else {
        alert(`Import failed: ${result.message}`);
      }
    } catch (error) {
      alert('Import failed: Invalid file format');
    }
  };

  const handleFileImport = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (e) => {
        const content = e.target?.result as string;
        setImportData(content);
        setImportDialog(true);
      };
      reader.readAsText(file);
    }
  };

  if (studyPlans.length === 0) {
    return (
      <Box sx={{ textAlign: 'center', py: 8 }}>
        <Typography variant="h6" color="text.secondary" gutterBottom>
          No Study Plans Yet
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
          Create your first study plan to start your interview preparation journey.
        </Typography>
        <Button variant="contained" onClick={onCreateNew}>
          Create Study Plan
        </Button>
      </Box>
    );
  }

  return (
    <Box>
      {/* Important: Export Reminder */}
      <Alert
        severity="info"
        icon={<DownloadIcon />}
        sx={{ mb: 3, bgcolor: 'primary.50' }}
        action={
          <Button
            color="primary"
            variant="contained"
            size="small"
            onClick={handleExport}
            startIcon={<DownloadIcon />}
          >
            Export Now
          </Button>
        }
      >
        <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
          Save your progress!
        </Typography>
        <Typography variant="body2">
          Study plans are stored in your browser. Export regularly to avoid losing your progress.
        </Typography>
      </Alert>

      {/* Storage Warning */}
      {storageWarning && (
        <Alert
          severity="warning"
          icon={<WarningIcon />}
          sx={{ mb: 3 }}
          action={
            <Button color="inherit" size="small" onClick={handleExport}>
              Export Data
            </Button>
          }
        >
          {storageWarning}
        </Alert>
      )}

      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h6">
          Your Study Plans ({studyPlans.length})
        </Typography>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button variant="contained" onClick={onCreateNew}>
            Create New Plan
          </Button>
          <IconButton onClick={(e) => setMenuAnchor(e.currentTarget)}>
            <MoreVertIcon />
          </IconButton>
        </Box>
      </Box>

      {/* Options Menu */}
      <Menu
        anchorEl={menuAnchor}
        open={Boolean(menuAnchor)}
        onClose={() => setMenuAnchor(null)}
      >
        <MenuItem onClick={handleExport}>
          <DownloadIcon sx={{ mr: 1 }} />
          Export All Plans
        </MenuItem>
        <MenuItem component="label">
          <UploadIcon sx={{ mr: 1 }} />
          Import Plans
          <input
            type="file"
            accept=".json"
            hidden
            onChange={handleFileImport}
          />
        </MenuItem>
      </Menu>

      <Box sx={{ 
        display: 'grid', 
        gridTemplateColumns: { xs: '1fr', md: 'repeat(2, 1fr)', lg: 'repeat(3, 1fr)' }, 
        gap: 3 
      }}>
        {studyPlans.map((plan) => {
          const timeRemaining = getTimeRemaining(plan);
          const progress = plan.progress;
          
          return (
            <Card 
              key={plan.id}
              sx={{ 
                height: '100%',
                display: 'flex',
                flexDirection: 'column',
                cursor: 'pointer',
                '&:hover': {
                  boxShadow: 4
                }
              }}
              onClick={() => onSelect(plan)}
            >
              <CardContent sx={{ flex: 1 }}>
                {/* Header */}
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                  <Typography variant="h6" sx={{ flex: 1, mr: 1 }}>
                    {plan.name}
                  </Typography>
                  <Box sx={{ display: 'flex', gap: 0.5 }}>
                    <IconButton 
                      size="small" 
                      onClick={(e) => {
                        e.stopPropagation();
                        onSelect(plan);
                      }}
                    >
                      <PlayArrowIcon fontSize="small" />
                    </IconButton>
                    <IconButton 
                      size="small" 
                      color="error"
                      onClick={(e) => {
                        e.stopPropagation();
                        onDelete(plan.id);
                      }}
                    >
                      <DeleteIcon fontSize="small" />
                    </IconButton>
                  </Box>
                </Box>

                {/* Companies */}
                <Stack direction="row" spacing={0.5} sx={{ mb: 2, flexWrap: 'wrap', gap: 0.5 }}>
                  {plan.targetCompanies.slice(0, 3).map(company => (
                    <Chip key={company} label={company} size="small" />
                  ))}
                  {plan.targetCompanies.length > 3 && (
                    <Chip 
                      label={`+${plan.targetCompanies.length - 3} more`} 
                      size="small" 
                      variant="outlined" 
                    />
                  )}
                </Stack>

                {/* Progress */}
                <Box sx={{ mb: 2 }}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                    <Typography variant="body2" color="text.secondary">
                      Progress
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      {progress.completedProblems}/{progress.totalProblems}
                    </Typography>
                  </Box>
                  <LinearProgress
                    variant="determinate"
                    value={progress.completionRate}
                    sx={{ height: 6, borderRadius: 3 }}
                  />
                  <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
                    {progress.completionRate.toFixed(1)}% complete
                  </Typography>
                </Box>

                {/* Stats */}
                <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 2, mb: 2 }}>
                  <Box>
                    <Typography variant="body2" color="text.secondary">
                      Daily Goal
                    </Typography>
                    <Typography variant="body1" fontWeight="medium">
                      {plan.dailyGoal} problems
                    </Typography>
                  </Box>
                  <Box>
                    <Typography variant="body2" color="text.secondary">
                      Current Streak
                    </Typography>
                    <Typography variant="body1" fontWeight="medium">
                      {progress.currentStreak} days
                    </Typography>
                  </Box>
                </Box>

                {/* Time Status */}
                <Box sx={{ mt: 'auto' }}>
                  {timeRemaining.status === 'completed' && (
                    <Alert severity="success" sx={{ py: 0.5 }}>
                      {timeRemaining.text}
                    </Alert>
                  )}
                  {timeRemaining.status === 'today' && (
                    <Alert severity="warning" sx={{ py: 0.5 }}>
                      {timeRemaining.text}
                    </Alert>
                  )}
                  {timeRemaining.status === 'ending' && (
                    <Alert severity="info" sx={{ py: 0.5 }}>
                      {timeRemaining.text}
                    </Alert>
                  )}
                  {timeRemaining.status === 'active' && (
                    <Typography variant="body2" color="text.secondary">
                      {timeRemaining.text}
                    </Typography>
                  )}
                </Box>

                {/* Created Date */}
                <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                  Created {formatDate(plan.createdAt)}
                </Typography>
              </CardContent>
            </Card>
          );
        })}
      </Box>

      {/* Import Dialog */}
      <Dialog open={importDialog} onClose={() => setImportDialog(false)} maxWidth="md" fullWidth>
        <DialogTitle>Import Study Plans</DialogTitle>
        <DialogContent>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            Paste the JSON content from your exported study plans file:
          </Typography>
          <TextField
            fullWidth
            multiline
            rows={10}
            value={importData}
            onChange={(e) => setImportData(e.target.value)}
            placeholder="Paste JSON content here..."
            variant="outlined"
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setImportDialog(false)}>Cancel</Button>
          <Button onClick={handleImport} variant="contained" disabled={!importData.trim()}>
            Import
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}