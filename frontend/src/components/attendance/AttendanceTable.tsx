import React, { useState } from 'react';
import {
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Box,
  Typography,
  IconButton,
  Collapse,
} from '@mui/material';
import {
  KeyboardArrowDown as KeyboardArrowDownIcon,
  KeyboardArrowUp as KeyboardArrowUpIcon,
  AccessTime as AccessTimeIcon,
} from '@mui/icons-material';
import { DailyAttendanceItem } from '../../services/types';
import { StatusChip } from '../common/StatusChip';
import { EmptyState } from '../common/EmptyState';

interface AttendanceTableProps {
  records: DailyAttendanceItem[];
}

const AttendanceRow: React.FC<{ item: DailyAttendanceItem }> = ({ item }) => {
  const [open, setOpen] = useState(false);

  return (
    <>
      <TableRow hover sx={{ '& > *': { borderBottom: 'unset' } }}>
        <TableCell sx={{ width: 48 }}>
          <IconButton size="small" onClick={() => setOpen(!open)}>
            {open ? <KeyboardArrowUpIcon fontSize="small" /> : <KeyboardArrowDownIcon fontSize="small" />}
          </IconButton>
        </TableCell>

        <TableCell>
          <Typography variant="body2" sx={{ fontWeight: 600, color: '#0F172A' }}>
            {item.name}
          </Typography>
          <Typography variant="caption" sx={{ fontFamily: 'monospace', color: 'text.secondary' }}>
            {item.employee_id}
          </Typography>
        </TableCell>

        <TableCell>
          <Typography variant="body2" sx={{ fontFamily: 'monospace', fontWeight: 600, color: item.check_in ? '#0F172A' : '#94A3B8' }}>
            {item.check_in || '—'}
          </Typography>
        </TableCell>

        <TableCell>
          <Typography variant="body2" sx={{ fontFamily: 'monospace', fontWeight: 600, color: item.check_out ? '#0F172A' : '#94A3B8' }}>
            {item.check_out || '—'}
          </Typography>
        </TableCell>

        <TableCell>
          <Typography variant="body2" sx={{ fontFamily: 'monospace', fontWeight: 600 }}>
            {item.working_hours !== null && item.working_hours !== undefined
              ? `${item.working_hours.toFixed(2)} hrs`
              : '—'}
          </Typography>
        </TableCell>

        <TableCell>
          <StatusChip status={item.status} />
        </TableCell>
      </TableRow>

      <TableRow>
        <TableCell style={{ paddingBottom: 0, paddingTop: 0 }} colSpan={6}>
          <Collapse in={open} timeout="auto" unmountOnExit>
            <Box sx={{ p: 2.5, my: 1, backgroundColor: '#F8FAFC', borderRadius: 2, border: '1px solid #E2E8F0' }}>
              <Typography variant="caption" sx={{ fontWeight: 700, color: '#475569', textTransform: 'uppercase', display: 'flex', alignItems: 'center', gap: 1, mb: 1.5 }}>
                <AccessTimeIcon sx={{ fontSize: 16, color: '#4338CA' }} />
                Biometric Punch Timeline & Telemetry
              </Typography>

              <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: 'repeat(3, 1fr)' }, gap: 2 }}>
                <Box sx={{ p: 1.5, backgroundColor: '#FFFFFF', borderRadius: 1.5, border: '1px solid #E2E8F0' }}>
                  <Typography variant="caption" color="text.secondary">First Scanner Verification</Typography>
                  <Typography variant="body2" sx={{ fontWeight: 600, color: item.check_in ? '#065F46' : '#94A3B8' }}>
                    {item.check_in ? `Entry: ${item.check_in}` : 'No entry scan recorded'}
                  </Typography>
                </Box>

                <Box sx={{ p: 1.5, backgroundColor: '#FFFFFF', borderRadius: 1.5, border: '1px solid #E2E8F0' }}>
                  <Typography variant="caption" color="text.secondary">Latest Checkout Verification</Typography>
                  <Typography variant="body2" sx={{ fontWeight: 600, color: item.check_out ? '#1E40AF' : '#94A3B8' }}>
                    {item.check_out ? `Exit: ${item.check_out}` : 'No checkout scan recorded'}
                  </Typography>
                </Box>

                <Box sx={{ p: 1.5, backgroundColor: '#FFFFFF', borderRadius: 1.5, border: '1px solid #E2E8F0' }}>
                  <Typography variant="caption" color="text.secondary">Attendance Health</Typography>
                  <Typography variant="body2" sx={{ fontWeight: 600 }}>
                    Status: <StatusChip status={item.status} sx={{ height: 20, fontSize: '0.7rem' }} />
                  </Typography>
                </Box>
              </Box>
            </Box>
          </Collapse>
        </TableCell>
      </TableRow>
    </>
  );
};

export const AttendanceTable: React.FC<AttendanceTableProps> = ({ records }) => {
  if (records.length === 0) {
    return (
      <EmptyState
        title="No Attendance Records"
        description="There are no attendance records for the selected date. Verify if scanner devices are active or check another date."
      />
    );
  }

  return (
    <TableContainer component={Paper} variant="outlined" sx={{ borderRadius: 3 }}>
      <Table sx={{ minWidth: 700 }}>
        <TableHead>
          <TableRow>
            <TableCell sx={{ width: 48 }} />
            <TableCell>Employee</TableCell>
            <TableCell>First In</TableCell>
            <TableCell>Last Out</TableCell>
            <TableCell>Hours Worked</TableCell>
            <TableCell>Daily Status</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {records.map((item) => (
            <AttendanceRow key={item.employee_id} item={item} />
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  );
};
