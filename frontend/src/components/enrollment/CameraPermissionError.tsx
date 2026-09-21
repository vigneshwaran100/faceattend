import React from 'react';
import { Box, Typography, Button, Paper } from '@mui/material';
import {
  VideocamOffOutlined as VideocamOffOutlinedIcon,
  Replay as ReplayIcon,
  CloudUploadOutlined as CloudUploadOutlinedIcon,
} from '@mui/icons-material';

interface CameraPermissionErrorProps {
  onRetry: () => void;
  onSwitchToUpload?: () => void;
  errorMessage?: string;
}

export const CameraPermissionError: React.FC<CameraPermissionErrorProps> = ({
  onRetry,
  onSwitchToUpload,
  errorMessage = 'Camera access was denied or no video input device was detected.',
}) => {
  return (
    <Paper
      elevation={0}
      sx={{
        p: 6,
        textAlign: 'center',
        border: '1px solid #FECACA',
        borderRadius: 3,
        backgroundColor: '#FEF2F2',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: 380,
      }}
    >
      <Box
        sx={{
          width: 64,
          height: 64,
          borderRadius: '50%',
          backgroundColor: '#FEE2E2',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: '#DC2626',
          mb: 2.5,
        }}
      >
        <VideocamOffOutlinedIcon sx={{ fontSize: 36 }} />
      </Box>

      <Typography variant="h5" sx={{ fontWeight: 700, color: '#991B1B', mb: 1 }}>
        Camera Permission Denied
      </Typography>

      <Typography variant="body2" sx={{ color: '#7F1D1D', maxWidth: 460, mb: 3 }}>
        {errorMessage} Please check your browser privacy settings and grant camera permissions to capture face enrollment samples.
      </Typography>

      <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', justifyContent: 'center' }}>
        <Button
          variant="contained"
          color="error"
          startIcon={<ReplayIcon />}
          onClick={onRetry}
          sx={{ fontWeight: 600 }}
        >
          Grant Permission & Retry
        </Button>

        {onSwitchToUpload && (
          <Button
            variant="outlined"
            sx={{
              borderColor: '#DC2626',
              color: '#DC2626',
              '&:hover': {
                borderColor: '#B91C1C',
                backgroundColor: '#FEE2E2',
              },
            }}
            startIcon={<CloudUploadOutlinedIcon />}
            onClick={onSwitchToUpload}
          >
            Upload Photo Instead
          </Button>
        )}
      </Box>
    </Paper>
  );
};
