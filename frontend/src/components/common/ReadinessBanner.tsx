import React from 'react';
import { Alert, Box, Button, Typography, Collapse } from '@mui/material';
import {
  WarningAmber as WarningAmberIcon,
  ErrorOutline as ErrorOutlineIcon,
  CheckCircleOutline as CheckCircleOutlineIcon,
} from '@mui/icons-material';
import { ReadinessStatus } from '../../services/types';

interface ReadinessBannerProps {
  status: ReadinessStatus;
  onRetry?: () => void;
}

export const ReadinessBanner: React.FC<ReadinessBannerProps> = ({ status, onRetry }) => {
  const isHealthy = status.status === 'ready';
  const isDegraded = status.status === 'degraded';
  const isNotReady = status.status === 'not_ready';

  if (isHealthy) {
    return null;
  }

  return (
    <Collapse in={!isHealthy}>
      <Box sx={{ mb: 3 }}>
        {isDegraded && (
          <Alert
            severity="warning"
            icon={<WarningAmberIcon />}
            action={
              onRetry && (
                <Button color="inherit" size="small" onClick={onRetry}>
                  Re-check
                </Button>
              )
            }
            sx={{
              borderRadius: 2,
              border: '1px solid #FDE68A',
              backgroundColor: '#FFFBEB',
              color: '#92400E',
            }}
          >
            <Typography variant="body2" sx={{ fontWeight: 600 }}>
              Degraded Service Readiness
            </Typography>
            <Typography variant="caption" sx={{ display: 'block', mt: 0.25 }}>
              Vector database (Milvus) is unreachable. Face enrollment is temporarily unavailable. Core attendance logs and records remain fully operational.
            </Typography>
          </Alert>
        )}

        {isNotReady && (
          <Alert
            severity="error"
            icon={<ErrorOutlineIcon />}
            action={
              onRetry && (
                <Button color="inherit" size="small" onClick={onRetry}>
                  Retry Connection
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
            <Typography variant="body2" sx={{ fontWeight: 600 }}>
              Critical Dependency Offline
            </Typography>
            <Typography variant="caption" sx={{ display: 'block', mt: 0.25 }}>
              Database service is unreachable. Application functionality is paused until connection is re-established.
            </Typography>
          </Alert>
        )}
      </Box>
    </Collapse>
  );
};
