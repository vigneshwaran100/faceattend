import React from 'react';
import { Box, Typography, Button, IconButton, Grid, Paper } from '@mui/material';
import {
  Replay as ReplayIcon,
  DeleteOutline as DeleteOutlineIcon,
} from '@mui/icons-material';
import { GUIDED_POSES, CapturedSample } from '../../services/types';

interface SampleGalleryProps {
  samples: CapturedSample[];
  onRetake: (stepId: number) => void;
  onClearAll: () => void;
}

export const SampleGallery: React.FC<SampleGalleryProps> = ({
  samples,
  onRetake,
  onClearAll,
}) => {
  return (
    <Box sx={{ mt: 3 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="subtitle1" sx={{ fontWeight: 700 }}>
          Captured Pose Thumbnails ({samples.length} / {GUIDED_POSES.length})
        </Typography>
        {samples.length > 0 && (
          <Button
            size="small"
            color="error"
            startIcon={<DeleteOutlineIcon fontSize="small" />}
            onClick={onClearAll}
          >
            Reset All
          </Button>
        )}
      </Box>

      <Grid container spacing={2}>
        {GUIDED_POSES.map((step) => {
          const sample = samples.find((s) => s.stepId === step.id);

          return (
            <Grid item xs={6} sm={4} md={2.4} key={step.id}>
              <Paper
                variant="outlined"
                sx={{
                  p: 1.5,
                  borderRadius: 2,
                  textAlign: 'center',
                  backgroundColor: sample ? '#FFFFFF' : '#F8FAFC',
                  border: sample ? '1px solid #CBD5E1' : '1px dashed #CBD5E1',
                  minHeight: 140,
                  display: 'flex',
                  flexDirection: 'column',
                  justifyContent: 'space-between',
                  position: 'relative',
                  overflow: 'hidden',
                }}
              >
                <Typography variant="caption" sx={{ fontWeight: 600, color: 'text.secondary', display: 'block', mb: 0.5 }}>
                  {step.label}
                </Typography>

                {sample ? (
                  <Box sx={{ position: 'relative', width: '100%', height: 80, borderRadius: 1.5, overflow: 'hidden' }}>
                    <img
                      src={sample.dataUrl}
                      alt={step.label}
                      style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                    />
                    <IconButton
                      size="small"
                      onClick={() => onRetake(step.id)}
                      sx={{
                        position: 'absolute',
                        bottom: 4,
                        right: 4,
                        backgroundColor: 'rgba(15, 23, 42, 0.75)',
                        color: '#FFFFFF',
                        p: 0.5,
                        '&:hover': {
                          backgroundColor: 'rgba(15, 23, 42, 0.95)',
                        },
                      }}
                      title="Retake sample"
                    >
                      <ReplayIcon sx={{ fontSize: 14 }} />
                    </IconButton>
                  </Box>
                ) : (
                  <Box
                    sx={{
                      height: 80,
                      borderRadius: 1.5,
                      backgroundColor: '#F1F5F9',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      color: '#94A3B8',
                      fontSize: '0.75rem',
                    }}
                  >
                    Awaiting
                  </Box>
                )}
              </Paper>
            </Grid>
          );
        })}
      </Grid>
    </Box>
  );
};
