import React, { useEffect } from 'react';
import { 
  Snackbar, 
  Alert, 
  AlertTitle,
  Button,
  Box
} from '@mui/material';
import { 
  Close as CloseIcon,
  Refresh as RefreshIcon 
} from '@mui/icons-material';

interface GlobalError {
  id: string;
  message: string;
  type: 'error' | 'warning' | 'info';
  details?: string;
  timestamp: number;
  canRetry?: boolean;
  onRetry?: () => void;
}

interface GlobalErrorHandlerProps {
  errors: GlobalError[];
  onDismiss: (id: string) => void;
  onRetry?: (id: string) => void;
}

export function GlobalErrorHandler({ 
  errors, 
  onDismiss, 
  onRetry 
}: GlobalErrorHandlerProps) {
  // Auto-dismiss info messages after 5 seconds
  useEffect(() => {
    const timers = errors
      .filter(error => error.type === 'info')
      .map(error => 
        setTimeout(() => onDismiss(error.id), 5000)
      );

    return () => {
      timers.forEach(timer => clearTimeout(timer));
    };
  }, [errors, onDismiss]);

  // Show the most recent error
  const currentError = errors[errors.length - 1];

  if (!currentError) {
    return null;
  }

  const handleRetry = () => {
    if (currentError.onRetry) {
      currentError.onRetry();
    } else if (onRetry) {
      onRetry(currentError.id);
    }
    onDismiss(currentError.id);
  };

  return (
    <Snackbar
      open={true}
      anchorOrigin={{ vertical: 'top', horizontal: 'right' }}
      sx={{ mt: 8 }} // Account for app header
    >
      <Alert
        severity={currentError.type}
        onClose={() => onDismiss(currentError.id)}
        sx={{ 
          minWidth: 400,
          maxWidth: 600,
          '& .MuiAlert-message': { 
            width: '100%' 
          }
        }}
        action={
          <Box sx={{ display: 'flex', gap: 1 }}>
            {currentError.canRetry && (
              <Button
                size="small"
                startIcon={<RefreshIcon />}
                onClick={handleRetry}
                color="inherit"
              >
                Retry
              </Button>
            )}
            <Button
              size="small"
              onClick={() => onDismiss(currentError.id)}
              color="inherit"
            >
              <CloseIcon fontSize="small" />
            </Button>
          </Box>
        }
      >
        <AlertTitle>
          {currentError.type === 'error' ? 'Error' : 
           currentError.type === 'warning' ? 'Warning' : 'Info'}
        </AlertTitle>
        {currentError.message}
        {currentError.details && (
          <Box 
            sx={{ 
              mt: 1, 
              p: 1, 
              backgroundColor: 'rgba(0,0,0,0.1)', 
              borderRadius: 1,
              fontSize: '0.875rem',
              fontFamily: 'monospace'
            }}
          >
            {currentError.details}
          </Box>
        )}
      </Alert>
    </Snackbar>
  );
}

// Error manager hook
export function useGlobalErrorHandler() {
  const [errors, setErrors] = React.useState<GlobalError[]>([]);

  const addError = React.useCallback((
    message: string, 
    type: GlobalError['type'] = 'error',
    options?: {
      details?: string;
      canRetry?: boolean;
      onRetry?: () => void;
    }
  ) => {
    const error: GlobalError = {
      id: `error-${Date.now()}-${Math.random()}`,
      message,
      type,
      details: options?.details,
      timestamp: Date.now(),
      canRetry: options?.canRetry,
      onRetry: options?.onRetry
    };

    setErrors(prev => [...prev, error]);
    return error.id;
  }, []);

  const dismissError = React.useCallback((id: string) => {
    setErrors(prev => prev.filter(error => error.id !== id));
  }, []);

  const clearAllErrors = React.useCallback(() => {
    setErrors([]);
  }, []);

  // Handle unhandled promise rejections
  React.useEffect(() => {
    const handleUnhandledRejection = (event: PromiseRejectionEvent) => {
      console.error('Unhandled promise rejection:', event.reason);
      addError(
        'An unexpected error occurred',
        'error',
        {
          details: event.reason?.message || String(event.reason),
          canRetry: true,
          onRetry: () => window.location.reload()
        }
      );
    };

    const handleError = (event: ErrorEvent) => {
      console.error('Global error:', event.error);
      addError(
        'A JavaScript error occurred',
        'error',
        {
          details: event.error?.message || event.message,
          canRetry: true,
          onRetry: () => window.location.reload()
        }
      );
    };

    window.addEventListener('unhandledrejection', handleUnhandledRejection);
    window.addEventListener('error', handleError);

    return () => {
      window.removeEventListener('unhandledrejection', handleUnhandledRejection);
      window.removeEventListener('error', handleError);
    };
  }, [addError]);

  return {
    errors,
    addError,
    dismissError,
    clearAllErrors
  };
}