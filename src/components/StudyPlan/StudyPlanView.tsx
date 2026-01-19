import { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Chip,
  LinearProgress,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  IconButton,
  Checkbox,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Stack,
  Tabs,
  Tab,
  Tooltip
} from '@mui/material';
import {
  ExpandMore as ExpandMoreIcon,
  CheckCircle as CheckCircleIcon,
  RadioButtonUnchecked as RadioButtonUncheckedIcon,
  SkipNext as SkipIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Launch as LaunchIcon,
  BookmarkBorder as BookmarkIcon,
  Bookmark as BookmarkedIcon,
  Dashboard as DashboardIcon,
  Schedule as ScheduleIcon,
  Article as ArticleIcon,
  Download as DownloadIcon,
  CalendarMonth as CalendarIcon,
  Print as PrintIcon
} from '@mui/icons-material';
import type { StudyPlan, StudySession, StudyProblem, ProblemData } from '../../types';
import { studyPlanService } from '../../services/studyPlanService';
import { ExportService } from '../../services/exportService';
import { StudyProgressDashboard } from './StudyProgressDashboard';
import { ProblemPreviewDrawer } from '../Common/ProblemPreviewDrawer';

interface StudyPlanViewProps {
  studyPlan: StudyPlan;
  onUpdate: (updatedPlan: StudyPlan) => void;
  onDelete: (planId: string) => void;
}

export function StudyPlanView({ studyPlan, onUpdate, onDelete }: StudyPlanViewProps) {
  const [selectedSession, setSelectedSession] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState(0);
  const [noteDialog, setNoteDialog] = useState<{
    open: boolean;
    sessionId: string;
    problemTitle: string;
    currentNotes: string;
  }>({
    open: false,
    sessionId: '',
    problemTitle: '',
    currentNotes: ''
  });
  const [previewProblem, setPreviewProblem] = useState<ProblemData | null>(null);
  const [previewOpen, setPreviewOpen] = useState(false);

  const handleProblemStatusChange = (
    sessionId: string,
    problemTitle: string,
    newStatus: StudyProblem['status']
  ) => {
    studyPlanService.updateProblemStatus(
      studyPlan.id,
      sessionId,
      problemTitle,
      newStatus
    );
    
    // Reload the updated plan
    const updatedPlan = studyPlanService.getStudyPlan(studyPlan.id);
    if (updatedPlan) {
      onUpdate(updatedPlan);
    }
  };

  const handleAddNote = (sessionId: string, problemTitle: string, currentNotes: string = '') => {
    setNoteDialog({
      open: true,
      sessionId,
      problemTitle,
      currentNotes
    });
  };

  const handleSaveNote = () => {
    const { sessionId, problemTitle, currentNotes } = noteDialog;
    
    studyPlanService.updateProblemStatus(
      studyPlan.id,
      sessionId,
      problemTitle,
      'in_progress', // Keep current status, just update notes
      currentNotes
    );

    const updatedPlan = studyPlanService.getStudyPlan(studyPlan.id);
    if (updatedPlan) {
      onUpdate(updatedPlan);
    }

    setNoteDialog({ open: false, sessionId: '', problemTitle: '', currentNotes: '' });
  };

  const handleToggleBookmark = (sessionId: string, problemTitle: string, currentNotes: string = '') => {
    const isBookmarked = currentNotes.includes('[BOOKMARK]');
    const newNotes = isBookmarked 
      ? currentNotes.replace('[BOOKMARK]', '').trim()
      : `[BOOKMARK] ${currentNotes}`.trim();
    
    studyPlanService.updateProblemStatus(
      studyPlan.id,
      sessionId,
      problemTitle,
      'in_progress', // Keep current status
      newNotes
    );

    const updatedPlan = studyPlanService.getStudyPlan(studyPlan.id);
    if (updatedPlan) {
      onUpdate(updatedPlan);
    }
  };

  const getStatusIcon = (status: StudyProblem['status']) => {
    switch (status) {
      case 'completed':
        return <CheckCircleIcon color="success" />;
      case 'skipped':
        return <SkipIcon color="warning" />;
      case 'in_progress':
        return <RadioButtonUncheckedIcon color="primary" />;
      default:
        return <RadioButtonUncheckedIcon color="disabled" />;
    }
  };

  const getDifficultyColor = (difficulty: string) => {
    switch (difficulty) {
      case 'EASY':
        return 'success';
      case 'MEDIUM':
        return 'warning';
      case 'HARD':
        return 'error';
      default:
        return 'default';
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      weekday: 'short',
      month: 'short',
      day: 'numeric'
    });
  };

  const isSessionOverdue = (session: StudySession) => {
    const sessionDate = new Date(session.date);
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    sessionDate.setHours(0, 0, 0, 0);
    
    return sessionDate < today && !session.completed;
  };

  const getSessionStatus = (session: StudySession) => {
    if (session.completed) return 'completed';
    if (isSessionOverdue(session)) return 'overdue';
    
    const today = new Date().toISOString().split('T')[0];
    if (session.date === today) return 'today';
    if (session.date > today) return 'upcoming';
    
    return 'pending';
  };

  const extractSlugFromLink = (link?: string) => {
    if (!link) {
      return null;
    }
    const match = link.match(/leetcode\.com\/problems\/([\w-]+)/i);
    return match ? match[1].toLowerCase() : null;
  };

  const generateSlugFromTitle = (title: string) => {
    return title
      .trim()
      .toLowerCase()
      .replace(/[^a-z0-9\s-]/g, '')
      .replace(/\s+/g, '-')
      .replace(/-+/g, '-');
  };

  const mapStudyProblemToPreview = (problem: StudyProblem): ProblemData => {
    const slugFromLink = extractSlugFromLink(problem.link);
    return {
      title: problem.title,
      titleSlug: slugFromLink || generateSlugFromTitle(problem.title),
      difficulty: problem.difficulty,
      topics: problem.topics,
      company: problem.company,
      link: problem.link,
      acceptanceRate: problem.acceptanceRate,
      likes: problem.likes,
      dislikes: problem.dislikes,
      originalityScore: problem.originalityScore,
      totalVotes: problem.totalVotes,
    };
  };

  const handleOpenPreview = (problem: StudyProblem) => {
    setPreviewProblem(mapStudyProblemToPreview(problem));
    setPreviewOpen(true);
  };

  const handleClosePreview = () => {
    setPreviewOpen(false);
    setPreviewProblem(null);
  };

  const progress = studyPlan.progress;

  return (
    <Box>
      {/* Study Plan Header */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
            <Box>
              <Typography variant="h5" gutterBottom>
                {studyPlan.name}
              </Typography>
              <Stack direction="row" spacing={1} sx={{ mb: 2 }}>
                {studyPlan.targetCompanies.map(company => (
                  <Chip key={company} label={company} size="small" />
                ))}
              </Stack>
            </Box>
            <Box sx={{ display: 'flex', gap: 1 }} className="no-print">
              <Tooltip title="Print / Save as PDF">
                <IconButton
                  size="small"
                  color="primary"
                  onClick={() => window.print()}
                >
                  <PrintIcon />
                </IconButton>
              </Tooltip>
              <Tooltip title="Add to Calendar (.ics)">
                <IconButton
                  size="small"
                  color="secondary"
                  onClick={() => ExportService.exportStudyPlanToICS(studyPlan)}
                >
                  <CalendarIcon />
                </IconButton>
              </Tooltip>
              <Tooltip title="Export as JSON">
                <IconButton
                  size="small"
                  color="primary"
                  onClick={() => {
                    const exportData = JSON.stringify({
                      exportDate: new Date().toISOString(),
                      version: '1.0',
                      studyPlans: [studyPlan]
                    }, null, 2);
                    const blob = new Blob([exportData], { type: 'application/json' });
                    const url = URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = `study-plan-${studyPlan.name.replace(/\s+/g, '-').toLowerCase()}-${new Date().toISOString().split('T')[0]}.json`;
                    document.body.appendChild(a);
                    a.click();
                    document.body.removeChild(a);
                    URL.revokeObjectURL(url);
                  }}
                >
                  <DownloadIcon />
                </IconButton>
              </Tooltip>
              <Tooltip title="Edit plan">
                <IconButton size="small" color="primary">
                  <EditIcon />
                </IconButton>
              </Tooltip>
              <Tooltip title="Delete plan">
                <IconButton
                  size="small"
                  color="error"
                  onClick={() => onDelete(studyPlan.id)}
                >
                  <DeleteIcon />
                </IconButton>
              </Tooltip>
            </Box>
          </Box>

          {/* Progress Overview */}
          <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: '2fr 1fr' }, gap: 3 }}>
            <Box>
              <Typography variant="subtitle2" gutterBottom>
                Overall Progress
              </Typography>
              <LinearProgress
                variant="determinate"
                value={progress.completionRate}
                sx={{ height: 8, borderRadius: 4, mb: 1 }}
              />
              <Typography variant="body2" color="text.secondary">
                {progress.completedProblems} of {progress.totalProblems} problems completed ({progress.completionRate.toFixed(1)}%)
              </Typography>
            </Box>
            
            <Stack spacing={1}>
              <Typography variant="body2">
                <strong>Current Streak:</strong> {progress.currentStreak} days
              </Typography>
              <Typography variant="body2">
                <strong>Longest Streak:</strong> {progress.longestStreak} days
              </Typography>
              <Typography variant="body2">
                <strong>Avg/Day:</strong> {progress.averageProblemsPerDay.toFixed(1)} problems
              </Typography>
            </Stack>
          </Box>

          {/* Difficulty Breakdown */}
          <Box sx={{ mt: 3 }}>
            <Typography variant="subtitle2" gutterBottom>
              Progress by Difficulty
            </Typography>
            <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 2 }}>
              {Object.entries(progress.difficultyBreakdown).map(([difficulty, stats]) => (
                <Box key={difficulty} sx={{ textAlign: 'center' }}>
                  <Chip
                    label={difficulty}
                    color={getDifficultyColor(difficulty) as any}
                    size="small"
                    sx={{ mb: 1 }}
                  />
                  <Typography variant="body2">
                    {stats.completed}/{stats.total}
                  </Typography>
                  <LinearProgress
                    variant="determinate"
                    value={stats.total > 0 ? (stats.completed / stats.total) * 100 : 0}
                    color={getDifficultyColor(difficulty) as any}
                    sx={{ height: 4, borderRadius: 2 }}
                  />
                </Box>
              ))}
            </Box>
          </Box>
        </CardContent>
      </Card>

      {/* Tabs for Dashboard and Schedule */}
      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
        <Tabs value={activeTab} onChange={(_, newValue) => setActiveTab(newValue)}>
          <Tab 
            icon={<DashboardIcon />} 
            label="Progress Dashboard" 
            iconPosition="start"
          />
          <Tab 
            icon={<ScheduleIcon />} 
            label="Study Schedule" 
            iconPosition="start"
          />
        </Tabs>
      </Box>

      {/* Tab Content */}
      {activeTab === 0 && (
        <StudyProgressDashboard 
          studyPlan={studyPlan} 
          onUpdate={onUpdate}
        />
      )}

      {activeTab === 1 && (
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Study Schedule
            </Typography>
          
          {studyPlan.schedule.map((session, index) => {
            const sessionStatus = getSessionStatus(session);
            const completedProblems = session.problems.filter(p => p.status === 'completed').length;
            
            return (
              <Accordion
                key={session.id}
                expanded={selectedSession === session.id}
                onChange={(_, isExpanded) => setSelectedSession(isExpanded ? session.id : null)}
                sx={{
                  mb: 1,
                  '&:before': { display: 'none' },
                  border: sessionStatus === 'overdue' ? '1px solid' : 'none',
                  borderColor: 'error.main',
                  bgcolor: sessionStatus === 'today' ? 'action.hover' : 'background.paper'
                }}
              >
                <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                  <Box sx={{ display: 'flex', alignItems: 'center', width: '100%' }}>
                    <Box sx={{ flex: 1 }}>
                      <Typography variant="subtitle1">
                        Day {index + 1} - {formatDate(session.date)}
                        {sessionStatus === 'today' && (
                          <Chip label="Today" size="small" color="primary" sx={{ ml: 1 }} />
                        )}
                        {sessionStatus === 'overdue' && (
                          <Chip label="Overdue" size="small" color="error" sx={{ ml: 1 }} />
                        )}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        {completedProblems}/{session.problems.length} problems completed
                      </Typography>
                    </Box>
                    
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <LinearProgress
                        variant="determinate"
                        value={(completedProblems / session.problems.length) * 100}
                        sx={{ width: 100, height: 6, borderRadius: 3 }}
                      />
                      {session.completed && <CheckCircleIcon color="success" />}
                    </Box>
                  </Box>
                </AccordionSummary>
                
                <AccordionDetails>
                  <List dense>
                    {session.problems.map((problem, problemIndex) => (
                      <ListItem key={problemIndex} divider>
                        <ListItemText
                          disableTypography
                          primary={
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                              <Typography variant="body1">
                                {problem.title}
                              </Typography>
                              <Chip
                                label={problem.difficulty}
                                size="small"
                                color={getDifficultyColor(problem.difficulty) as any}
                              />
                              <Chip
                                label={problem.company}
                                size="small"
                                variant="outlined"
                              />
                            </Box>
                          }
                          secondary={
                            <Box sx={{ mt: 1 }}>
                              <Typography variant="body2" color="text.secondary">
                                Topics: {problem.topics.join(', ')}
                              </Typography>
                              
                              {/* Quality Metrics Display */}
                              {problem.qualityScore && (
                                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 0.5, flexWrap: 'wrap' }}>
                                  <Chip
                                    label={`Quality: ${(problem.qualityScore * 100).toFixed(0)}%`}
                                    size="small"
                                    color={problem.qualityScore >= 0.8 ? 'success' : problem.qualityScore >= 0.6 ? 'primary' : 'default'}
                                    variant="outlined"
                                  />
                                  
                                  {problem.qualityTier && problem.qualityTier !== 'Unknown' && (
                                    <Chip
                                      label={problem.qualityTier}
                                      size="small"
                                      color={
                                        problem.qualityTier === 'Premium' ? 'success' :
                                        problem.qualityTier === 'High' ? 'primary' :
                                        problem.qualityTier === 'Good' ? 'secondary' : 'default'
                                      }
                                      variant="outlined"
                                    />
                                  )}
                                  
                                  {problem.isInterviewClassic && (
                                    <Chip
                                      label="Interview Classic"
                                      size="small"
                                      color="warning"
                                      variant="outlined"
                                    />
                                  )}
                                  
                                  {problem.isHiddenGem && (
                                    <Chip
                                      label="Hidden Gem"
                                      size="small"
                                      color="success"
                                      variant="outlined"
                                    />
                                  )}
                                  
                                  {problem.likes && problem.likes > 0 && (
                                    <Typography variant="caption" color="text.secondary">
                                      👍 {problem.likes.toLocaleString()}
                                    </Typography>
                                  )}
                                  
                                  {problem.acceptanceRate && (
                                    <Typography variant="caption" color="text.secondary">
                                      Acceptance: {(problem.acceptanceRate * 100).toFixed(1)}%
                                    </Typography>
                                  )}
                                </Box>
                              )}
                              
                              {problem.recommendationReason && (
                                <Typography variant="caption" color="primary" sx={{ mt: 0.5, display: 'block' }}>
                                  💡 {problem.recommendationReason}
                                </Typography>
                              )}
                              
                              {problem.notes && (
                                <Typography variant="body2" sx={{ mt: 0.5, fontStyle: 'italic' }}>
                                  Notes: {problem.notes}
                                </Typography>
                              )}
                            </Box>
                          }
                        />
                        
                        <ListItemSecondaryAction>
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                            <Tooltip title={problem.notes?.includes('[BOOKMARK]') ? 'Remove bookmark' : 'Add bookmark'}>
                              <IconButton
                                size="small"
                                onClick={() => handleToggleBookmark(session.id, problem.title, problem.notes)}
                                color={problem.notes?.includes('[BOOKMARK]') ? 'secondary' : 'default'}
                              >
                                {problem.notes?.includes('[BOOKMARK]') ? 
                                  <BookmarkedIcon fontSize="small" /> : 
                                  <BookmarkIcon fontSize="small" />
                                }
                              </IconButton>
                            </Tooltip>

                            <Tooltip title="Preview problem">
                              <IconButton
                                size="small"
                                onClick={() => handleOpenPreview(problem)}
                              >
                                <ArticleIcon fontSize="small" />
                              </IconButton>
                            </Tooltip>
                            
                            <Tooltip title="Add notes">
                              <IconButton
                                size="small"
                                onClick={() => handleAddNote(session.id, problem.title, problem.notes)}
                              >
                                <EditIcon fontSize="small" />
                              </IconButton>
                            </Tooltip>
                            
                            <Tooltip title={problem.link ? 'Open problem' : 'Problem link unavailable'}>
                              <span>
                                {problem.link ? (
                                  <IconButton
                                    size="small"
                                    component="a"
                                    href={problem.link}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                  >
                                    <LaunchIcon fontSize="small" />
                                  </IconButton>
                                ) : (
                                  <IconButton size="small" disabled>
                                    <LaunchIcon fontSize="small" />
                                  </IconButton>
                                )}
                              </span>
                            </Tooltip>
                            
                            <Tooltip title="Mark as completed">
                              <Checkbox
                                checked={problem.status === 'completed'}
                                onChange={(e) => 
                                  handleProblemStatusChange(
                                    session.id,
                                    problem.title,
                                    e.target.checked ? 'completed' : 'not_started'
                                  )
                                }
                                icon={getStatusIcon(problem.status)}
                                checkedIcon={<CheckCircleIcon color="success" />}
                              />
                            </Tooltip>
                            
                            <Button
                              size="small"
                              variant="outlined"
                              color="warning"
                              onClick={() => 
                                handleProblemStatusChange(session.id, problem.title, 'skipped')
                              }
                              disabled={problem.status === 'skipped'}
                            >
                              Skip
                            </Button>
                          </Box>
                        </ListItemSecondaryAction>
                      </ListItem>
                    ))}
                  </List>
                </AccordionDetails>
              </Accordion>
            );
          })}
        </CardContent>
      </Card>
      )}

      {/* Notes Dialog */}
      <Dialog
        open={noteDialog.open}
        onClose={() => setNoteDialog({ ...noteDialog, open: false })}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Add Notes</DialogTitle>
        <DialogContent>
          <TextField
            fullWidth
            multiline
            rows={4}
            label="Notes"
            value={noteDialog.currentNotes}
            onChange={(e) => setNoteDialog({ ...noteDialog, currentNotes: e.target.value })}
            placeholder="Add your thoughts, approach, or key learnings..."
            sx={{ mt: 1 }}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setNoteDialog({ ...noteDialog, open: false })}>
            Cancel
          </Button>
          <Button onClick={handleSaveNote} variant="contained">
            Save
          </Button>
        </DialogActions>
      </Dialog>

      <ProblemPreviewDrawer
        open={previewOpen}
        problem={previewProblem}
        onClose={handleClosePreview}
      />
    </Box>
  );
}
