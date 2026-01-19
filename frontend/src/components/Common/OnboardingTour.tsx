import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Typography,
  Box,
  Stepper,
  Step,
  StepLabel,

  Card,
  CardContent,
  Chip,
  IconButton
} from '@mui/material';
import {
  Close as CloseIcon,
  NavigateNext as NextIcon,
  NavigateBefore as BackIcon,
  Business as CompanyIcon,
  TrendingUp as TrendingIcon,
  School as StudyIcon,
  Analytics as AnalyticsIcon,
  Star as StarIcon,
  CheckCircle as CheckIcon
} from '@mui/icons-material';

interface OnboardingStep {
  title: string;
  description: string;
  icon: React.ReactNode;
  features: string[];
  highlight?: string;
}

const onboardingSteps: OnboardingStep[] = [
  {
    title: 'Welcome to Interview Prep Dashboard',
    description: 'Your comprehensive tool for data-driven interview preparation with insights from 18,668+ real problems across 470+ companies.',
    icon: <StarIcon sx={{ fontSize: 40, color: 'primary.main' }} />,
    features: [
      'Real interview data from top tech companies',
      'Smart analytics and insights',
      'Personalized study plans',
      'Quality-based problem recommendations'
    ],
    highlight: 'Get started with evidence-based interview prep!'
  },
  {
    title: 'Company Research',
    description: 'Analyze company-specific interview patterns and get targeted preparation strategies.',
    icon: <CompanyIcon sx={{ fontSize: 40, color: 'info.main' }} />,
    features: [
      'Company-specific problem statistics',
      'Difficulty distribution analysis',
      'Topic frequency insights',
      'FAANG comparison tools'
    ],
    highlight: 'Research your target companies to focus your preparation'
  },
  {
    title: 'Topic Analysis',
    description: 'Discover trending topics and understand which skills are most in-demand.',
    icon: <TrendingIcon sx={{ fontSize: 40, color: 'success.main' }} />,
    features: [
      'Topic popularity trends',
      'Cross-company topic analysis',
      'Emerging skill identification',
      'Topic correlation insights'
    ],
    highlight: 'Stay ahead with trending topics and skills'
  },
  {
    title: 'Smart Study Planner',
    description: 'Generate personalized study plans based on your target companies and timeline.',
    icon: <StudyIcon sx={{ fontSize: 40, color: 'warning.main' }} />,
    features: [
      'Customized study schedules',
      'Progress tracking',
      'Quality-aware recommendations',
      'Adaptive difficulty progression'
    ],
    highlight: 'Create efficient, data-driven study plans'
  },
  {
    title: 'Advanced Analytics',
    description: 'Leverage powerful analytics to optimize your preparation strategy.',
    icon: <AnalyticsIcon sx={{ fontSize: 40, color: 'secondary.main' }} />,
    features: [
      'Problem quality analysis',
      'Hidden gems discovery',
      'Performance correlations',
      'Predictive insights'
    ],
    highlight: 'Make data-driven decisions about your preparation'
  }
];

interface OnboardingTourProps {
  open: boolean;
  onClose: () => void;
  onComplete: () => void;
}

export function OnboardingTour({ open, onClose, onComplete }: OnboardingTourProps) {
  const [activeStep, setActiveStep] = useState(0);
  const [completed, setCompleted] = useState<Set<number>>(new Set());

  const handleNext = () => {
    if (activeStep === onboardingSteps.length - 1) {
      handleComplete();
    } else {
      setCompleted(prev => new Set(prev).add(activeStep));
      setActiveStep(prev => prev + 1);
    }
  };

  const handleBack = () => {
    setActiveStep(prev => prev - 1);
  };

  const handleComplete = () => {
    setCompleted(prev => new Set(prev).add(activeStep));
    onComplete();
    onClose();
  };

  const handleSkip = () => {
    onClose();
  };

  const currentStep = onboardingSteps[activeStep];

  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="md"
      fullWidth
      PaperProps={{
        sx: { 
          borderRadius: 2,
          minHeight: 500
        }
      }}
    >
      <DialogTitle sx={{ 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center',
        pb: 1
      }}>
        <Typography variant="h5" component="span">
          Getting Started
        </Typography>
        <IconButton onClick={onClose} size="small">
          <CloseIcon />
        </IconButton>
      </DialogTitle>

      <DialogContent sx={{ pb: 2 }}>
        <Box sx={{ mb: 3 }}>
          <Stepper activeStep={activeStep} alternativeLabel>
            {onboardingSteps.map((step, index) => (
              <Step key={step.title} completed={completed.has(index)}>
                <StepLabel>
                  {step.title.split(' ').slice(0, 2).join(' ')}
                </StepLabel>
              </Step>
            ))}
          </Stepper>
        </Box>

        <Card elevation={2} sx={{ mb: 3 }}>
          <CardContent sx={{ textAlign: 'center', py: 4 }}>
            <Box sx={{ mb: 2 }}>
              {currentStep.icon}
            </Box>
            
            <Typography variant="h4" component="h3" gutterBottom>
              {currentStep.title}
            </Typography>
            
            <Typography variant="body1" color="text.secondary" sx={{ mb: 3, maxWidth: 500, mx: 'auto' }}>
              {currentStep.description}
            </Typography>

            {currentStep.highlight && (
              <Chip 
                label={currentStep.highlight}
                color="primary"
                variant="outlined"
                sx={{ mb: 3 }}
              />
            )}

            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, justifyContent: 'center' }}>
              {currentStep.features.map((feature, index) => (
                <Box 
                  key={index}
                  sx={{ 
                    display: 'flex', 
                    alignItems: 'center', 
                    gap: 0.5,
                    backgroundColor: 'grey.50',
                    px: 2,
                    py: 0.5,
                    borderRadius: 1,
                    border: '1px solid',
                    borderColor: 'grey.200'
                  }}
                >
                  <CheckIcon sx={{ fontSize: 16, color: 'success.main' }} />
                  <Typography variant="body2">
                    {feature}
                  </Typography>
                </Box>
              ))}
            </Box>
          </CardContent>
        </Card>

        <Box sx={{ 
          display: 'flex', 
          justifyContent: 'center',
          gap: 1,
          mb: 2
        }}>
          {onboardingSteps.map((_, index) => (
            <Box
              key={index}
              sx={{
                width: 8,
                height: 8,
                borderRadius: '50%',
                backgroundColor: index === activeStep ? 'primary.main' : 
                                completed.has(index) ? 'success.main' : 'grey.300',
                transition: 'background-color 0.3s'
              }}
            />
          ))}
        </Box>
      </DialogContent>

      <DialogActions sx={{ px: 3, pb: 3, justifyContent: 'space-between' }}>
        <Button onClick={handleSkip} color="inherit">
          Skip Tour
        </Button>
        
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button
            onClick={handleBack}
            disabled={activeStep === 0}
            startIcon={<BackIcon />}
          >
            Back
          </Button>
          
          <Button
            onClick={handleNext}
            variant="contained"
            endIcon={activeStep === onboardingSteps.length - 1 ? <CheckIcon /> : <NextIcon />}
          >
            {activeStep === onboardingSteps.length - 1 ? 'Get Started' : 'Next'}
          </Button>
        </Box>
      </DialogActions>
    </Dialog>
  );
}

// Hook for managing onboarding state
export function useOnboarding() {
  const [hasSeenOnboarding, setHasSeenOnboarding] = useState(() => {
    return localStorage.getItem('hasSeenOnboarding') === 'true';
  });

  const [showOnboarding, setShowOnboarding] = useState(false);

  useEffect(() => {
    if (!hasSeenOnboarding) {
      // Show onboarding after a short delay to let the app load
      const timer = setTimeout(() => {
        setShowOnboarding(true);
      }, 1000);

      return () => clearTimeout(timer);
    }
  }, [hasSeenOnboarding]);

  const completeOnboarding = () => {
    setHasSeenOnboarding(true);
    setShowOnboarding(false);
    localStorage.setItem('hasSeenOnboarding', 'true');
  };

  const resetOnboarding = () => {
    setHasSeenOnboarding(false);
    localStorage.removeItem('hasSeenOnboarding');
  };

  const startOnboarding = () => {
    setShowOnboarding(true);
  };

  return {
    showOnboarding,
    hasSeenOnboarding,
    completeOnboarding,
    resetOnboarding,
    startOnboarding,
    closeOnboarding: () => setShowOnboarding(false)
  };
}