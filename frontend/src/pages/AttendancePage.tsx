import React, { useState } from 'react';
import {
  Box,
  Typography,
  Button,
  Card,
  TextField,
  Stack,
  Chip,
} from '@mui/material';
import {
  DownloadOutlined as DownloadOutlinedIcon,
  Today as TodayIcon,
} from '@mui/icons-material';
import { AttendanceTable } from '../components/attendance/AttendanceTable';
import { ErrorAlert } from '../components/common/ErrorAlert';
import { LoadingSkeleton } from '../components/common/LoadingSkeleton';
import { attendanceService } from '../services/attendanceService';
import { DailyAttendanceItemResponse } from '../types/api';

export const AttendancePage: React.FC = () => {
  const [selectedDate, setSelectedDate] = useState(
    new Date().toISOString().split('T')[0]
  );
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [records, setRecords] = useState<DailyAttendanceItemResponse[]>([]);

  const fetchAttendance = async () => {
    setLoading(true);
    setError(null);
    try {
      const report = await attendanceService.getDailyReport(selectedDate);
      setRecords(report.records || []);
    } catch (err: any) {
      setError(err.message || 'Failed to load daily attendance matrix.');
    } finally {
      setLoading(false);
    }
  };

  React.useEffect(() => {
    fetchAttendance();
  }, [selectedDate]);

  const filteredRecords = records.filter((r) => {
    if (!statusFilter) return true;
    return r.status === statusFilter;
  });

  const handleExportCSV = () => {
    const headers = ['Employee ID', 'Name', 'Check-In', 'Check-Out', 'Working Hours', 'Status'];
    const rows = filteredRecords.map((r) => [
      r.employee_id,
      r.name,
      r.check_in || 'N/A',
      r.check_out || 'N/A',
      r.working_hours ? r.working_hours.toFixed(2) : 'N/A',
      r.status.toUpperCase(),
    ]);

    const csvContent =
      'data:text/csv;charset=utf-8,' +
      [headers.join(','), ...rows.map((e) => e.join(','))].join('\n');

    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', `attendance_report_${selectedDate}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  if (loading && records.length === 0) {
    return <LoadingSkeleton />;
  }

  return (
    <Box>
      {error && (
        <Box sx={{ mb: 3 }}>
          <ErrorAlert
            title="Attendance Telemetry Error"
            message={error}
            onRetry={fetchAttendance}
            onClose={() => setError(null)}
          />
        </Box>
      )}
      {/* Top Header */}
      <Box sx={{ display: 'flex', flexDirection: { xs: 'column', sm: 'row' }, justifyContent: 'space-between', alignItems: { xs: 'flex-start', sm: 'center' }, gap: 2, mb: 3.5 }}>
        <Box>
          <Typography variant="h2" sx={{ fontWeight: 800, color: '#0F172A', mb: 0.5 }}>
            Daily Attendance Matrix & Timecards
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Daily organizational punch verification, working hours, and shift compliance records
          </Typography>
        </Box>

        <Button
          variant="contained"
          color="primary"
          startIcon={<DownloadOutlinedIcon />}
          onClick={handleExportCSV}
          sx={{ bgcolor: '#4338CA' }}
        >
          Export CSV Report
        </Button>
      </Box>

      {/* Date and Status Filter Toolbar */}
      <Card sx={{ p: 2.5, mb: 3, borderRadius: 3 }}>
        <Stack direction={{ xs: 'column', md: 'row' }} spacing={2.5} alignItems="center" justifyContent="space-between">
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, width: { xs: '100%', md: 'auto' } }}>
            <TextField
              type="date"
              label="Select Attendance Date"
              value={selectedDate}
              onChange={(e) => setSelectedDate(e.target.value)}
              InputLabelProps={{ shrink: true }}
              sx={{ minWidth: 220 }}
            />
            <Button
              variant="outlined"
              size="small"
              startIcon={<TodayIcon />}
              onClick={() => setSelectedDate(new Date().toISOString().split('T')[0])}
            >
              Today
            </Button>
          </Box>

          {/* Quick Filter Status Chips */}
          <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
            <Chip
              label={`All (${records.length})`}
              clickable
              variant={statusFilter === '' ? 'filled' : 'outlined'}
              color={statusFilter === '' ? 'primary' : 'default'}
              onClick={() => setStatusFilter('')}
            />
            <Chip
              label="Present"
              clickable
              variant={statusFilter === 'present' ? 'filled' : 'outlined'}
              color={statusFilter === 'present' ? 'success' : 'default'}
              onClick={() => setStatusFilter(statusFilter === 'present' ? '' : 'present')}
            />
            <Chip
              label="In Progress"
              clickable
              variant={statusFilter === 'in_progress' ? 'filled' : 'outlined'}
              color={statusFilter === 'in_progress' ? 'primary' : 'default'}
              onClick={() => setStatusFilter(statusFilter === 'in_progress' ? '' : 'in_progress')}
            />
            <Chip
              label="Half Day"
              clickable
              variant={statusFilter === 'half_day' ? 'filled' : 'outlined'}
              color={statusFilter === 'half_day' ? 'warning' : 'default'}
              onClick={() => setStatusFilter(statusFilter === 'half_day' ? '' : 'half_day')}
            />
            <Chip
              label="Incomplete"
              clickable
              variant={statusFilter === 'incomplete' ? 'filled' : 'outlined'}
              color={statusFilter === 'incomplete' ? 'warning' : 'default'}
              onClick={() => setStatusFilter(statusFilter === 'incomplete' ? '' : 'incomplete')}
            />
            <Chip
              label="Absent"
              clickable
              variant={statusFilter === 'absent' ? 'filled' : 'outlined'}
              color={statusFilter === 'absent' ? 'error' : 'default'}
              onClick={() => setStatusFilter(statusFilter === 'absent' ? '' : 'absent')}
            />
          </Box>
        </Stack>
      </Card>

      {/* Attendance Data Table */}
      <AttendanceTable records={filteredRecords} />
    </Box>
  );
};
