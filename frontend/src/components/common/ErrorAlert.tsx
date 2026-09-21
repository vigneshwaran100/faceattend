import React from 'react';
import { Alert, AlertTitle, Button, Box } from '@mui/material';
import { Replay as ReplayIcon } from '@mui/icons-material';

interface ErrorAlertProps {
  title?: string;
  message: string;
  onRetry?: () => void;
  onClose?: () => void;
}

export const ErrorAlert: React.FC<ErrorAlertProps> = ({
  title = 'An error occurred',
  message,
  onRetry,
  onClose,
}) => {
  return (
    <Box sx={{ my: 2 }}>
      <Alert
        severity="error"
        onClose={onClose}
        action={
          onRetry && (
            <Button
              color="inherit"
              size="small"
              startIcon={<ReplayIcon fontSize="small" />}
              onClick={onRetry}
              sx={{ fontWeight: 600 }}
            >
              Retry
            </Button>
          )
        }
        sx={{
          borderRadius: 2,
          border: '1px solid #FECACA',
          backgroundColor: '#FEF2F2',
          color: '#991B1B',
        }}
      >
        <AlertTitle sx={{ fontWeight: 600, mb: 0.5 }}>{title}</AlertTitle>
        {message}
      </Alert>
    </Box>
  );
};
