import React from 'react';
import {
  Box,
  Typography,
  Paper,
  Button,
  Divider,
  Chip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow
} from '@mui/material';
import {
  Print as PrintIcon,
  Close as CloseIcon
} from '@mui/icons-material';
import type { StudyPlan, ProblemData, CompanyData } from '../../types';

interface PrintViewProps {
  data: StudyPlan | ProblemData[] | CompanyData[];
  dataType: 'studyPlan' | 'problems' | 'companies';
  title: string;
  onClose: () => void;
}

const PrintableStudyPlan: React.FC<{ studyPlan: StudyPlan }> = ({ studyPlan }) => {
  const problems = studyPlan.schedule.flatMap(session => session.problems);
  
  return (
    <Box>
      <Typography variant="h4" gutterBottom sx={{ '@media print': { fontSize: '1.5rem' } }}>
        Study Plan: {studyPlan.name}
      </Typography>
      
      <Box sx={{ mb: 3, display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 2 }}>
        <Box>
          <Typography variant="h6" gutterBottom>Plan Details</Typography>
          <Typography variant="body2"><strong>Target Companies:</strong> {studyPlan.targetCompanies.join(', ')}</Typography>
          <Typography variant="body2"><strong>Duration:</strong> {studyPlan.duration} weeks</Typography>
          <Typography variant="body2"><strong>Daily Goal:</strong> {studyPlan.dailyGoal} problems per day</Typography>
          <Typography variant="body2"><strong>Focus Areas:</strong> {studyPlan.focusAreas.join(', ')}</Typography>
          <Typography variant="body2"><strong>Created:</strong> {new Date(studyPlan.createdAt).toLocaleDateString()}</Typography>
        </Box>
        
        <Box>
          <Typography variant="h6" gutterBottom>Progress Summary</Typography>
          <Typography variant="body2"><strong>Total Problems:</strong> {studyPlan.progress.totalProblems}</Typography>
          <Typography variant="body2"><strong>Completed:</strong> {studyPlan.progress.completedProblems}</Typography>
          <Typography variant="body2"><strong>Completion Rate:</strong> {studyPlan.progress.completionRate.toFixed(1)}%</Typography>
          <Typography variant="body2"><strong>Current Streak:</strong> {studyPlan.progress.currentStreak} days</Typography>
        </Box>
      </Box>

      <Divider sx={{ my: 2 }} />

      <Typography variant="h6" gutterBottom>Problems by Difficulty</Typography>
      <Box sx={{ mb: 3, display: 'flex', gap: 2, flexWrap: 'wrap' }}>
        <Chip 
          label={`Easy: ${studyPlan.progress.difficultyBreakdown.EASY.completed}/${studyPlan.progress.difficultyBreakdown.EASY.total}`}
          color="success"
          size="small"
        />
        <Chip 
          label={`Medium: ${studyPlan.progress.difficultyBreakdown.MEDIUM.completed}/${studyPlan.progress.difficultyBreakdown.MEDIUM.total}`}
          color="warning"
          size="small"
        />
        <Chip 
          label={`Hard: ${studyPlan.progress.difficultyBreakdown.HARD.completed}/${studyPlan.progress.difficultyBreakdown.HARD.total}`}
          color="error"
          size="small"
        />
      </Box>

      <Divider sx={{ my: 2 }} />

      <Typography variant="h6" gutterBottom>Problem List</Typography>
      <TableContainer component={Paper} sx={{ '@media print': { boxShadow: 'none' } }}>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Status</TableCell>
              <TableCell>Problem</TableCell>
              <TableCell>Difficulty</TableCell>
              <TableCell>Topics</TableCell>
              <TableCell>Company</TableCell>
              <TableCell>Notes</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {problems.map((problem, index) => {
              const statusIcon = problem.status === 'completed' ? '✅' : 
                               problem.status === 'skipped' ? '⏭️' : 
                               problem.status === 'in_progress' ? '🔄' : '⭕';
              
              return (
                <TableRow key={index}>
                  <TableCell>{statusIcon}</TableCell>
                  <TableCell>{problem.title}</TableCell>
                  <TableCell>
                    <Chip 
                      label={problem.difficulty} 
                      size="small"
                      color={
                        problem.difficulty === 'EASY' ? 'success' :
                        problem.difficulty === 'MEDIUM' ? 'warning' :
                        problem.difficulty === 'HARD' ? 'error' : 'default'
                      }
                    />
                  </TableCell>
                  <TableCell>{problem.topics.slice(0, 3).join(', ')}</TableCell>
                  <TableCell>{problem.company}</TableCell>
                  <TableCell>{problem.notes || '—'}</TableCell>
                </TableRow>
              );
            })}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  );
};

const PrintableProblems: React.FC<{ problems: ProblemData[] }> = ({ problems }) => {
  return (
    <Box>
      <Typography variant="h4" gutterBottom sx={{ '@media print': { fontSize: '1.5rem' } }}>
        Problems List ({problems.length} problems)
      </Typography>
      
      <TableContainer component={Paper} sx={{ '@media print': { boxShadow: 'none' } }}>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Problem</TableCell>
              <TableCell>Difficulty</TableCell>
              <TableCell>Company</TableCell>
              <TableCell>Topics</TableCell>
              <TableCell>Company Count</TableCell>
              <TableCell>Acceptance Rate</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {problems.map((problem, index) => (
              <TableRow key={index}>
                <TableCell>{problem.title}</TableCell>
                <TableCell>
                  <Chip 
                    label={problem.difficulty} 
                    size="small"
                    color={
                      problem.difficulty === 'EASY' ? 'success' :
                      problem.difficulty === 'MEDIUM' ? 'warning' :
                      problem.difficulty === 'HARD' ? 'error' : 'default'
                    }
                  />
                </TableCell>
                <TableCell>{problem.company}</TableCell>
                <TableCell>{problem.topics.slice(0, 3).join(', ')}</TableCell>
                <TableCell>{problem.companyCount?.toLocaleString() || '—'}</TableCell>
                <TableCell>{problem.acceptanceRate ? `${(problem.acceptanceRate * 100).toFixed(1)}%` : '—'}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  );
};

const PrintableCompanies: React.FC<{ companies: CompanyData[] }> = ({ companies }) => {
  return (
    <Box>
      <Typography variant="h4" gutterBottom sx={{ '@media print': { fontSize: '1.5rem' } }}>
        Companies List ({companies.length} companies)
      </Typography>
      
      <TableContainer component={Paper} sx={{ '@media print': { boxShadow: 'none' } }}>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Company</TableCell>
              <TableCell>Total Problems</TableCell>
              <TableCell>Unique Problems</TableCell>
              <TableCell>Avg Frequency</TableCell>
              <TableCell>Avg Acceptance Rate</TableCell>
              <TableCell>Top Topics</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {companies.map((company, index) => (
              <TableRow key={index}>
                <TableCell>{company.company}</TableCell>
                <TableCell>{company.totalProblems}</TableCell>
                <TableCell>{company.uniqueProblems}</TableCell>
                <TableCell>{company.avgFrequency.toFixed(1)}</TableCell>
                <TableCell>{(company.avgAcceptanceRate * 100).toFixed(1)}%</TableCell>
                <TableCell>{company.topTopics.slice(0, 3).join(', ')}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  );
};

export const PrintView: React.FC<PrintViewProps> = ({ data, dataType, title, onClose }) => {
  const handlePrint = () => {
    window.print();
  };

  const renderContent = () => {
    switch (dataType) {
      case 'studyPlan':
        return <PrintableStudyPlan studyPlan={data as StudyPlan} />;
      case 'problems':
        return <PrintableProblems problems={data as ProblemData[]} />;
      case 'companies':
        return <PrintableCompanies companies={data as CompanyData[]} />;
      default:
        return <Typography>Unsupported data type for printing</Typography>;
    }
  };

  return (
    <Box sx={{ 
      p: 3,
      '@media print': {
        p: 0,
        '& .no-print': { display: 'none' }
      }
    }}>
      {/* Print Controls - Hidden when printing */}
      <Box className="no-print" sx={{ mb: 3, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography variant="h5">{title}</Typography>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button
            variant="contained"
            startIcon={<PrintIcon />}
            onClick={handlePrint}
          >
            Print
          </Button>
          <Button
            variant="outlined"
            startIcon={<CloseIcon />}
            onClick={onClose}
          >
            Close
          </Button>
        </Box>
      </Box>

      {/* Print Content */}
      {renderContent()}

      {/* Print Footer */}
      <Box sx={{ 
        mt: 4, 
        pt: 2, 
        borderTop: 1, 
        borderColor: 'divider',
        '@media print': { 
          position: 'fixed', 
          bottom: 0, 
          left: 0, 
          right: 0,
          p: 1,
          fontSize: '0.8rem'
        }
      }}>
        <Typography variant="caption" color="text.secondary">
          Generated on {new Date().toLocaleDateString()} • Interview Prep Dashboard
        </Typography>
      </Box>
    </Box>
  );
};

export default PrintView;
