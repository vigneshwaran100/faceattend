import React from 'react';
import { Chip, ChipProps, Box } from '@mui/material';
import { AttendanceStatus } from '../../services/types';

interface StatusChipProps extends Omit<ChipProps, 'color'> {
  status: AttendanceStatus | 'active' | 'inactive' | 'SUCCESS' | 'FAILURE' | string;
}

export const StatusChip: React.FC<StatusChipProps> = ({ status, sx, ...props }) => {
  const normalized = (status || '').toLowerCase();

  let label = status;
  let bg = '#F1F5F9';
  let text = '#475569';
  let border = '#E2E8F0';
  let dotColor = '#94A3B8';

  switch (normalized) {
    case 'in_progress':
      label = 'In Progress';
      bg = '#EFF6FF';
      text = '#1E40AF';
      border = '#BFDBFE';
      dotColor = '#3B82F6';
      break;
    case 'present':
      label = 'Present';
      bg = '#ECFDF5';
      text = '#065F46';
      border = '#A7F3D0';
      dotColor = '#10B981';
      break;
    case 'half_day':
      label = 'Half Day';
      bg = '#FFFBEB';
      text = '#92400E';
      border = '#FDE68A';
      dotColor = '#F59E0B';
      break;
    case 'incomplete':
      label = 'Incomplete';
      bg = '#FFF7ED';
      text = '#9A3412';
      border = '#FED7AA';
      dotColor = '#F97316';
      break;
    case 'absent':
      label = 'Absent';
      bg = '#FEF2F2';
      text = '#991B1B';
      border = '#FECACA';
      dotColor = '#EF4444';
      break;
    case 'active':
      label = 'Active';
      bg = '#ECFDF5';
      text = '#065F46';
      border = '#A7F3D0';
      dotColor = '#10B981';
      break;
    case 'inactive':
      label = 'Inactive';
      bg = '#F8FAFC';
      text = '#64748B';
      border = '#CBD5E1';
      dotColor = '#94A3B8';
      break;
    case 'success':
      label = 'SUCCESS';
      bg = '#ECFDF5';
      text = '#065F46';
      border = '#A7F3D0';
      dotColor = '#10B981';
      break;
    case 'failure':
      label = 'FAILURE';
      bg = '#FEF2F2';
      text = '#991B1B';
      border = '#FECACA';
      dotColor = '#EF4444';
      break;
    default:
      label = status;
      break;
  }

  return (
    <Chip
      label={
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.75 }}>
          <Box
            sx={{
              width: 6,
              height: 6,
              borderRadius: '50%',
              backgroundColor: dotColor,
            }}
          />
          <span>{label}</span>
        </Box>
      }
      sx={{
        backgroundColor: bg,
        color: text,
        border: `1px solid ${border}`,
        fontWeight: 600,
        fontSize: '0.75rem',
        height: 24,
        ...sx,
      }}
      {...props}
    />
  );
};
