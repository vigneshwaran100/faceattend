import React from 'react';
import { Box, Chip, Typography } from '@mui/material';
import {
  CenterFocusStrong as CenterFocusStrongIcon,
  CheckCircleOutline as CheckCircleOutlineIcon,
  Cameraswitch as CameraswitchIcon,
  WarningAmber as WarningAmberIcon,
} from '@mui/icons-material';

export type CaptureState =
  | 'position_face'
  | 'align_face'
  | 'ready'
  | 'capturing'
  | 'captured'
  | 'retake'
  | 'warning';

interface CaptureStatusHUDProps {
  currentPoseLabel: string;
  instruction: string;
  captureState: CaptureState;
  liveStatusMessage?: string;
  liveYawAngle?: number;
  livePitchAngle?: number;
}

export const CaptureStatusHUD: React.FC<CaptureStatusHUDProps> = ({
  currentPoseLabel,
  instruction,
  captureState,
  liveStatusMessage,
  liveYawAngle = 0,
  livePitchAngle = 0,
}) => {
  let statusChipLabel = 'Position your face';
  let chipBg = '#F1F5F9';
  let chipText = '#475569';
  let chipBorder = '#CBD5E1';
  let icon = <CenterFocusStrongIcon sx={{ fontSize: 16 }} />;

  switch (captureState) {
    case 'position_face':
      statusChipLabel = 'Detecting Face';
      chipBg = '#F1F5F9';
      chipText = '#475569';
      chipBorder = '#CBD5E1';
      icon = <CenterFocusStrongIcon sx={{ fontSize: 16 }} />;
      break;
    case 'align_face':
      statusChipLabel = 'Align within Oval';
      chipBg = '#FFFBEB';
      chipText = '#92400E';
      chipBorder = '#FDE68A';
      icon = <CameraswitchIcon sx={{ fontSize: 16 }} />;
      break;
    case 'ready':
      statusChipLabel = 'Ready to capture';
      chipBg = '#ECFDF5';
      chipText = '#065F46';
      chipBorder = '#A7F3D0';
      icon = <CheckCircleOutlineIcon sx={{ fontSize: 16 }} />;
      break;
    case 'capturing':
      statusChipLabel = 'Capturing Sample...';
      chipBg = '#ECFDF5';
      chipText = '#065F46';
      chipBorder = '#A7F3D0';
      icon = <CameraswitchIcon sx={{ fontSize: 16 }} />;
      break;
    case 'captured':
      statusChipLabel = 'Sample Captured';
      chipBg = '#ECFDF5';
      chipText = '#065F46';
      chipBorder = '#A7F3D0';
      icon = <CheckCircleOutlineIcon sx={{ fontSize: 16 }} />;
      break;
    case 'retake':
      statusChipLabel = 'Retake Sample';
      chipBg = '#FFF7ED';
      chipText = '#9A3412';
      chipBorder = '#FED7AA';
      icon = <CameraswitchIcon sx={{ fontSize: 16 }} />;
      break;
    case 'warning':
      statusChipLabel = 'Multiple Faces';
      chipBg = '#FEF2F2';
      chipText = '#991B1B';
      chipBorder = '#FECACA';
      icon = <WarningAmberIcon sx={{ fontSize: 16 }} />;
      break;
  }

  return (
    <Box
      sx={{
        position: 'absolute',
        top: 16,
        left: 16,
        right: 16,
        zIndex: 10,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        pointerEvents: 'none',
      }}
    >
      <Box
        sx={{
          backgroundColor: 'rgba(11, 15, 25, 0.82)',
          backdropFilter: 'blur(12px)',
          border: '1px solid rgba(255, 255, 255, 0.12)',
          borderRadius: 3,
          px: 2.5,
          py: 1.25,
          textAlign: 'center',
          boxShadow: '0 8px 32px rgba(0, 0, 0, 0.4)',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: 0.75,
          maxWidth: '90%',
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flexWrap: 'wrap', justifyContent: 'center' }}>
          <Chip
            size="small"
            label={`Target: ${currentPoseLabel}`}
            sx={{
              backgroundColor: 'rgba(99, 102, 241, 0.25)',
              color: '#C7D2FE',
              border: '1px solid rgba(99, 102, 241, 0.4)',
              fontWeight: 700,
              fontSize: '0.75rem',
            }}
          />
          <Chip
            size="small"
            icon={icon}
            label={statusChipLabel}
            sx={{
              backgroundColor: chipBg,
              color: chipText,
              border: `1px solid ${chipBorder}`,
              fontWeight: 700,
              fontSize: '0.75rem',
            }}
          />
          <Chip
            size="small"
            label={`Yaw: ${liveYawAngle > 0 ? `+${liveYawAngle}` : liveYawAngle}° | Pitch: ${livePitchAngle > 0 ? `+${livePitchAngle}` : livePitchAngle}°`}
            sx={{
              backgroundColor: 'rgba(15, 23, 42, 0.6)',
              color: '#94A3B8',
              border: '1px solid rgba(148, 163, 184, 0.2)',
              fontFamily: 'monospace',
              fontSize: '0.7rem',
            }}
          />
        </Box>

        <Typography
          variant="body1"
          sx={{
            color: '#FFFFFF',
            fontWeight: 700,
            textShadow: '0 2px 6px rgba(0,0,0,0.6)',
            fontSize: '0.95rem',
          }}
        >
          {liveStatusMessage || instruction}
        </Typography>
      </Box>
    </Box>
  );
};
