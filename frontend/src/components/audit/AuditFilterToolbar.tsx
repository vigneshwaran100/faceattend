import React from 'react';
import { Box, TextField, MenuItem, Button, Stack } from '@mui/material';
import {
  FilterAltOutlined as FilterAltOutlinedIcon,
  Clear as ClearIcon,
} from '@mui/icons-material';

interface AuditFilterToolbarProps {
  scannerType: string;
  eventType: string;
  employeeId: string;
  startDate: string;
  endDate: string;
  onScannerTypeChange: (val: string) => void;
  onEventTypeChange: (val: string) => void;
  onEmployeeIdChange: (val: string) => void;
  onStartDateChange: (val: string) => void;
  onEndDateChange: (val: string) => void;
  onReset: () => void;
}

export const AuditFilterToolbar: React.FC<AuditFilterToolbarProps> = ({
  scannerType,
  eventType,
  employeeId,
  startDate,
  endDate,
  onScannerTypeChange,
  onEventTypeChange,
  onEmployeeIdChange,
  onStartDateChange,
  onEndDateChange,
  onReset,
}) => {
  return (
    <Box sx={{ p: 2.5, backgroundColor: '#FFFFFF', borderRadius: 3, border: '1px solid #E2E8F0', mb: 3 }}>
      <Stack direction={{ xs: 'column', md: 'row' }} spacing={2} alignItems="center">
        <TextField
          select
          label="Scanner Mode"
          value={scannerType}
          onChange={(e) => onScannerTypeChange(e.target.value)}
          sx={{ minWidth: 150 }}
        >
          <MenuItem value="">All Scanners</MenuItem>
          <MenuItem value="CHECK_IN">CHECK_IN (Entry)</MenuItem>
          <MenuItem value="CHECK_OUT">CHECK_OUT (Exit)</MenuItem>
          <MenuItem value="SYSTEM">SYSTEM (Orchestration)</MenuItem>
        </TextField>

        <TextField
          label="Event Type"
          placeholder="e.g. unknown_face"
          value={eventType}
          onChange={(e) => onEventTypeChange(e.target.value)}
          sx={{ minWidth: 160 }}
        />

        <TextField
          label="Employee ID"
          placeholder="e.g. EMP-1042"
          value={employeeId}
          onChange={(e) => onEmployeeIdChange(e.target.value)}
          sx={{ minWidth: 150 }}
        />

        <TextField
          type="date"
          label="From Date"
          value={startDate}
          onChange={(e) => onStartDateChange(e.target.value)}
          InputLabelProps={{ shrink: true }}
          sx={{ minWidth: 140 }}
        />

        <TextField
          type="date"
          label="To Date"
          value={endDate}
          onChange={(e) => onEndDateChange(e.target.value)}
          InputLabelProps={{ shrink: true }}
          sx={{ minWidth: 140 }}
        />

        <Button
          variant="outlined"
          color="secondary"
          startIcon={<ClearIcon />}
          onClick={onReset}
          sx={{ height: 40, whiteSpace: 'nowrap' }}
        >
          Reset Filters
        </Button>
      </Stack>
    </Box>
  );
};
