import React from 'react';
import { Box, Typography, LinearProgress, Stack } from '@mui/material';
import {
  CheckCircle as CheckCircleIcon,
  RadioButtonUnchecked as RadioButtonUncheckedIcon,
} from '@mui/icons-material';
import { GUIDED_POSES, CapturedSample } from '../../services/types';

interface PoseGuidanceHUDProps {
  currentStepIndex: number;
  capturedSamples: CapturedSample[];
}

export const PoseGuidanceHUD: React.FC<PoseGuidanceHUDProps> = ({
  currentStepIndex,
  capturedSamples,
}) => {
  const progressPercent = (capturedSamples.length / GUIDED_POSES.length) * 100;

  return (
    <Box sx={{ p: 2.5, backgroundColor: '#FFFFFF', borderRadius: 3, border: '1px solid #E2E8F0' }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1.5 }}>
        <Typography variant="subtitle2" sx={{ fontWeight: 700, color: '#0F172A' }}>
          Biometric Multi-Pose Sequence
        </Typography>
        <Typography variant="caption" sx={{ fontWeight: 600, color: 'primary.main', fontFeatureSettings: '"tnum" 1' }}>
          {capturedSamples.length} / {GUIDED_POSES.length} Samples Enrolled
        </Typography>
      </Box>

      <LinearProgress
        variant="determinate"
        value={progressPercent}
        sx={{
          height: 8,
          borderRadius: 4,
          backgroundColor: '#F1F5F9',
          mb: 2.5,
          '& .MuiLinearProgress-bar': {
            backgroundColor: '#10B981',
            borderRadius: 4,
          },
        }}
      />

      <Stack spacing={1}>
        {GUIDED_POSES.map((step, idx) => {
          const isCaptured = capturedSamples.some((s) => s.stepId === step.id);
          const isCurrent = currentStepIndex === idx;

          let bg = '#F8FAFC';
          let border = '#E2E8F0';
          let textColor = '#64748B';

          if (isCaptured) {
            bg = '#ECFDF5';
            border = '#A7F3D0';
            textColor = '#065F46';
          } else if (isCurrent) {
            bg = '#EEF2FF';
            border = '#C7D2FE';
            textColor = '#4338CA';
          }

          return (
            <Box
              key={step.id}
              sx={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                px: 2,
                py: 1.25,
                borderRadius: 2,
                backgroundColor: bg,
                border: `1px solid ${border}`,
                transition: 'all 0.2s',
              }}
            >
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
                {isCaptured ? (
                  <CheckCircleIcon sx={{ fontSize: 18, color: '#10B981' }} />
                ) : (
                  <RadioButtonUncheckedIcon
                    sx={{
                      fontSize: 18,
                      color: isCurrent ? '#4338CA' : '#94A3B8',
                    }}
                  />
                )}
                <Typography
                  variant="body2"
                  sx={{
                    fontWeight: isCurrent ? 700 : 500,
                    color: textColor,
                    fontSize: '0.8125rem',
                  }}
                >
                  {step.label}
                </Typography>
              </Box>

              <Typography variant="caption" sx={{ color: isCurrent ? '#4338CA' : '#94A3B8', fontWeight: isCurrent ? 600 : 400 }}>
                {isCaptured ? 'Captured' : isCurrent ? 'Active' : 'Pending'}
              </Typography>
            </Box>
          );
        })}
      </Stack>
    </Box>
  );
};
