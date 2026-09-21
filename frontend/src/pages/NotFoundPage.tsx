import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Box, Typography, Button, Paper } from '@mui/material';
import { HomeOutlined as HomeOutlinedIcon } from '@mui/icons-material';

export const NotFoundPage: React.FC = () => {
  const navigate = useNavigate();

  return (
    <Box
      sx={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: '60vh',
        p: 3,
      }}
    >
      <Paper
        elevation={0}
        sx={{
          p: 6,
          textAlign: 'center',
          maxWidth: 480,
          borderRadius: 4,
          border: '1px solid #E2E8F0',
        }}
      >
        <Typography
          variant="h1"
          sx={{
            fontWeight: 900,
            fontSize: '4rem',
            color: '#4338CA',
            fontFamily: 'monospace',
            mb: 1,
          }}
        >
          404
        </Typography>

        <Typography variant="h4" sx={{ fontWeight: 700, mb: 1.5 }}>
          Page Not Found
        </Typography>

        <Typography variant="body2" color="text.secondary" sx={{ mb: 3.5 }}>
          The requested route does not exist or has been moved within the enterprise shell.
        </Typography>

        <Button
          variant="contained"
          color="primary"
          startIcon={<HomeOutlinedIcon />}
          onClick={() => navigate('/dashboard')}
        >
          Return to Dashboard
        </Button>
      </Paper>
    </Box>
  );
};
