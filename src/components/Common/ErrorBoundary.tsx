import React, { Component, type ReactNode } from 'react';
import { 
  Box, 
  Typography, 
  Button, 
  Paper,
  Alert,
  AlertTitle,
  Collapse
} from '@mui/material';
import { 
  Error as ErrorIcon,
  Refresh as RefreshIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
  BugReport as BugReportIcon
} from '@mui/icons-material';

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
  errorInfo: React.ErrorInfo | null;
  showDetails: boolean;
}

interface ErrorBoundaryProps {
  children: ReactNode;
  fallback?: ReactNode;
  onError?: (error: Error, errorInfo: React.ErrorInfo) => void;
}

export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
      showDetails: false
    };
  }

  static getDerivedStateFromError(error: Error): Partial<ErrorBoundaryState> {
    return {
      hasError: true,
      error
    };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    this.setState({
      error,
      errorInfo
    });

    // Log error to console in development
    if (import.meta.env.DEV) {
      console.error('ErrorBoundary caught an error:', error, errorInfo);
    }

    // Call optional error handler
    this.props.onError?.(error, errorInfo);
  }

  handleRetry = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
      showDetails: false
    });
  };

  toggleDetails = () => {
    this.setState(prev => ({ showDetails: !prev.showDetails }));
  };

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <Box sx={{ p: 3, maxWidth: 800, mx: 'auto' }}>
          <Paper 
            elevation={3}
            sx={{ 
              p: 4, 
              border: '1px solid',
              borderColor: 'error.light',
              backgroundColor: 'error.50'
            }}
          >
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3 }}>
              <ErrorIcon color="error" sx={{ fontSize: 40 }} />
              <Box>
                <Typography variant="h5" component="h2" color="error.main">
                  Oops! Something went wrong
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  The application encountered an unexpected error
                </Typography>
              </Box>
            </Box>

            <Alert severity="error" sx={{ mb: 3 }}>
              <AlertTitle>Error Details</AlertTitle>
              <Typography variant="body2">
                {this.state.error?.message || 'An unknown error occurred'}
              </Typography>
            </Alert>

            <Box sx={{ display: 'flex', gap: 2, mb: 2 }}>
              <Button
                variant="contained"
                startIcon={<RefreshIcon />}
                onClick={this.handleRetry}
                color="primary"
              >
                Try Again
              </Button>
              
              <Button
                variant="outlined"
                startIcon={this.state.showDetails ? <ExpandLessIcon /> : <ExpandMoreIcon />}
                onClick={this.toggleDetails}
                color="inherit"
              >
                {this.state.showDetails ? 'Hide' : 'Show'} Technical Details
              </Button>
            </Box>

            <Collapse in={this.state.showDetails}>
              <Paper 
                variant="outlined" 
                sx={{ 
                  p: 2, 
                  backgroundColor: 'grey.50',
                  border: '1px solid',
                  borderColor: 'grey.300'
                }}
              >
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                  <BugReportIcon fontSize="small" />
                  <Typography variant="subtitle2" fontWeight="bold">
                    Technical Information
                  </Typography>
                </Box>
                
                {this.state.error && (
                  <Box sx={{ mb: 2 }}>
                    <Typography variant="caption" color="text.secondary">
                      Error Message:
                    </Typography>
                    <Typography 
                      variant="body2" 
                      sx={{ 
                        fontFamily: 'monospace',
                        backgroundColor: 'grey.100',
                        p: 1,
                        borderRadius: 1,
                        mt: 0.5
                      }}
                    >
                      {this.state.error.message}
                    </Typography>
                  </Box>
                )}

                {this.state.error?.stack && (
                  <Box sx={{ mb: 2 }}>
                    <Typography variant="caption" color="text.secondary">
                      Stack Trace:
                    </Typography>
                    <Typography 
                      variant="body2" 
                      sx={{ 
                        fontFamily: 'monospace',
                        backgroundColor: 'grey.100',
                        p: 1,
                        borderRadius: 1,
                        mt: 0.5,
                        fontSize: '0.75rem',
                        whiteSpace: 'pre-wrap',
                        maxHeight: 200,
                        overflow: 'auto'
                      }}
                    >
                      {this.state.error.stack}
                    </Typography>
                  </Box>
                )}

                {this.state.errorInfo?.componentStack && (
                  <Box>
                    <Typography variant="caption" color="text.secondary">
                      Component Stack:
                    </Typography>
                    <Typography 
                      variant="body2" 
                      sx={{ 
                        fontFamily: 'monospace',
                        backgroundColor: 'grey.100',
                        p: 1,
                        borderRadius: 1,
                        mt: 0.5,
                        fontSize: '0.75rem',
                        whiteSpace: 'pre-wrap',
                        maxHeight: 200,
                        overflow: 'auto'
                      }}
                    >
                      {this.state.errorInfo.componentStack}
                    </Typography>
                  </Box>
                )}
              </Paper>
            </Collapse>

            <Box sx={{ mt: 3, p: 2, backgroundColor: 'info.50', borderRadius: 1 }}>
              <Typography variant="body2" color="text.secondary">
                <strong>What can you do?</strong>
                <br />
                • Try refreshing the page
                <br />
                • Check your internet connection
                <br />
                • If the problem persists, the issue may be temporary
              </Typography>
            </Box>
          </Paper>
        </Box>
      );
    }

    return this.props.children;
  }
}

// Higher-order component for wrapping components with error boundary
export function withErrorBoundary<P extends object>(
  Component: React.ComponentType<P>,
  errorBoundaryProps?: Omit<ErrorBoundaryProps, 'children'>
) {
  const WrappedComponent = (props: P) => (
    <ErrorBoundary {...errorBoundaryProps}>
      <Component {...props} />
    </ErrorBoundary>
  );

  WrappedComponent.displayName = `withErrorBoundary(${Component.displayName || Component.name})`;
  
  return WrappedComponent;
}

// Hook for error reporting
export function useErrorHandler() {
  const handleError = React.useCallback((error: Error, context?: string) => {
    console.error(`Error${context ? ` in ${context}` : ''}:`, error);
    
    // In a real app, you might want to send this to an error reporting service
    // like Sentry, LogRocket, etc.
  }, []);

  return handleError;
}