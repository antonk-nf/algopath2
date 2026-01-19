import { ThemeProvider } from '@mui/material/styles';
import { CssBaseline } from '@mui/material';
import { theme } from './theme/theme';
import { AppProvider } from './context/AppContext';
import { AppLayout } from './components/Layout';
import { AppRouter } from './components';
import { ErrorBoundary } from './components/Common/ErrorBoundary';
import { GlobalErrorHandler, useGlobalErrorHandler } from './components/Common/GlobalErrorHandler';
import { OnboardingTour, useOnboarding } from './components/Common/OnboardingTour';
import { config, isFeatureEnabled, logger } from './config/environment';

function AppContent() {
  const { errors, dismissError } = useGlobalErrorHandler();
  const {
    showOnboarding,
    completeOnboarding,
    closeOnboarding
  } = useOnboarding();

  return (
    <>
      <AppLayout>
        <AppRouter />
      </AppLayout>
      
      {/* Global Error Handler */}
      <GlobalErrorHandler
        errors={errors}
        onDismiss={dismissError}
      />
      
      {/* Onboarding Tour */}
      {isFeatureEnabled('enableOnboarding') && (
        <OnboardingTour
          open={showOnboarding}
          onClose={closeOnboarding}
          onComplete={completeOnboarding}
        />
      )}
    </>
  );
}

function App() {
  // Log app startup in development
  if (config.debugMode) {
    logger.info('Interview Prep Dashboard starting...', {
      version: config.version,
      environment: config.appEnv,
      buildTime: config.buildTime
    });
  }

  return (
    <ErrorBoundary
      onError={(error, errorInfo) => {
        logger.error('Application error boundary triggered:', error, errorInfo);
        
        // In production, you might want to send this to an error reporting service
        if (isFeatureEnabled('enableErrorReporting')) {
          // Send to error reporting service (e.g., Sentry)
          console.error('Error reported to monitoring service:', error);
        }
      }}
    >
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <AppProvider>
          <AppContent />
        </AppProvider>
      </ThemeProvider>
    </ErrorBoundary>
  );
}

export default App;
