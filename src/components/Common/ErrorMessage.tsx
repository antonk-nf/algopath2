
import { 
  Box, 
  Alert, 
  AlertTitle, 
  Button, 
  Typography,
  Paper 
} from '@mui/material';
import { 
  Refresh as RefreshIcon,
  Error as ErrorIcon 
} from '@mui/icons-material';

interface ErrorMessageProps {
  title?: string;
  message: string;
  details?: string;
  onRetry?: () => void;
  retryLabel?: string;
  variant?: 'alert' | 'card';
}

export function ErrorMessage({
  title = 'Something went wrong',
  message,
  details,
  onRetry,
  retryLabel = 'Try Again',
  variant = 'alert'
}: ErrorMessageProps) {
  const content = (
    <>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
        <ErrorIcon color="error" />
        <Typography variant="h6" component="h3">
          {title}
        </Typography>
      </Box>
      
      <Typography variant="body1" sx={{ mb: details ? 1 : 2 }}>
        {message}
      </Typography>
      
      {details && (
        <Typography 
          variant="body2" 
          color="text.secondary" 
          sx={{ 
            mb: 2,
            fontFamily: 'monospace',
            backgroundColor: 'grey.100',
            p: 1,
            borderRadius: 1,
            fontSize: '0.875rem'
          }}
        >
          {details}
        </Typography>
      )}
      
      {onRetry && (
        <Button
          variant="outlined"
          startIcon={<RefreshIcon />}
          onClick={onRetry}
          size="small"
        >
          {retryLabel}
        </Button>
      )}
    </>
  );

  if (variant === 'card') {
    return (
      <Paper 
        sx={{ 
          p: 3, 
          border: '1px solid',
          borderColor: 'error.light',
          backgroundColor: 'error.50'
        }}
      >
        {content}
      </Paper>
    );
  }

  return (
    <Alert 
      severity="error" 
      sx={{ 
        '& .MuiAlert-message': { 
          width: '100%' 
        } 
      }}
    >
      <AlertTitle>{title}</AlertTitle>
      <Typography variant="body2" sx={{ mb: details ? 1 : 2 }}>
        {message}
      </Typography>
      
      {details && (
        <Typography 
          variant="body2" 
          sx={{ 
            mb: 2,
            fontFamily: 'monospace',
            backgroundColor: 'rgba(0,0,0,0.1)',
            p: 1,
            borderRadius: 1,
            fontSize: '0.75rem'
          }}
        >
          {details}
        </Typography>
      )}
      
      {onRetry && (
        <Button
          variant="outlined"
          startIcon={<RefreshIcon />}
          onClick={onRetry}
          size="small"
          color="error"
        >
          {retryLabel}
        </Button>
      )}
    </Alert>
  );
}