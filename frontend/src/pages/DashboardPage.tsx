import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Typography,
  Button,
  Grid,
  Card,
  CardContent,
  Stack,
  Avatar,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
} from '@mui/material';
import {
  PeopleAltOutlined as PeopleAltOutlinedIcon,
  CheckCircleOutline as CheckCircleOutlineIcon,
  HourglassEmpty as HourglassEmptyIcon,
  HighlightOff as HighlightOffIcon,
  PersonAddOutlined as PersonAddOutlinedIcon,
  FactCheckOutlined as FactCheckOutlinedIcon,
  FlashOn as FlashOnIcon,
} from '@mui/icons-material';
import { MetricCard } from '../components/common/MetricCard';
import { StatusChip } from '../components/common/StatusChip';
import { ConfirmDialog } from '../components/common/ConfirmDialog';
import { EmployeeDrawer } from '../components/employees/EmployeeDrawer';
import { ErrorAlert } from '../components/common/ErrorAlert';
import { EmptyState } from '../components/common/EmptyState';
import { LoadingSkeleton } from '../components/common/LoadingSkeleton';
import { attendanceService } from '../services/attendanceService';
import { employeeService } from '../services/employeeService';
import { DailyAttendanceItemResponse, EmployeeCreateRequest } from '../types/api';

export const DashboardPage: React.FC = () => {
  const navigate = useNavigate();
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [eodDialogOpen, setEodDialogOpen] = useState(false);
  const [eodLoading, setEodLoading] = useState(false);
  const [eodSuccessBanner, setEodSuccessBanner] = useState(false);
  const [eodMessage, setEodMessage] = useState('');

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [attendanceRecords, setAttendanceRecords] = useState<DailyAttendanceItemResponse[]>([]);
  const [totalEmployees, setTotalEmployees] = useState(0);

  // Today's Date formatted
  const todayFormatted = new Date().toLocaleDateString('en-US', {
    weekday: 'long',
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  });

  const fetchDashboardData = async () => {
    setLoading(true);
    setError(null);
    try {
      const todayIso = new Date().toISOString().split('T')[0];
      const report = await attendanceService.getDailyReport(todayIso);
      setAttendanceRecords(report.records || []);
      setTotalEmployees(report.total_employees || report.records?.length || 0);
    } catch (err: any) {
      setError(err.message || 'Failed to load daily attendance telemetry.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const presentCount = attendanceRecords.filter((r) => r.status === 'present').length;
  const inProgressCount = attendanceRecords.filter((r) => r.status === 'in_progress').length;
  const halfDayCount = attendanceRecords.filter((r) => r.status === 'half_day').length;
  const absentCount = attendanceRecords.filter((r) => r.status === 'absent').length;

  const handleEODConfirm = async () => {
    setEodLoading(true);
    try {
      const result = await attendanceService.finalizeEndOfDay();
      setEodDialogOpen(false);
      setEodMessage(result.message || 'End-of-day attendance finalization completed successfully.');
      setEodSuccessBanner(true);
      await fetchDashboardData();
    } catch (err: any) {
      setError(err.message || 'End-of-day finalization failed.');
      setEodDialogOpen(false);
    } finally {
      setEodLoading(false);
    }
  };

  const handleAddEmployee = async (newEmp: EmployeeCreateRequest) => {
    try {
      await employeeService.createEmployee(newEmp);
      setDrawerOpen(false);
      await fetchDashboardData();
    } catch (err: any) {
      throw err; // drawer will catch and display error
    }
  };

  if (loading && attendanceRecords.length === 0) {
    return <LoadingSkeleton />;
  }

  return (
    <Box>
      {error && (
        <Box sx={{ mb: 3 }}>
          <ErrorAlert
            title="Telemetry Error"
            message={error}
            onRetry={fetchDashboardData}
            onClose={() => setError(null)}
          />
        </Box>
      )}
      {/* Top Page Header */}
      <Box sx={{ display: 'flex', flexDirection: { xs: 'column', md: 'row' }, justifyContent: 'space-between', alignItems: { xs: 'flex-start', md: 'center' }, gap: 2, mb: 3.5 }}>
        <Box>
          <Typography variant="h2" sx={{ fontWeight: 800, color: '#0F172A', mb: 0.5 }}>
            Executive Operations Center
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Daily Attendance Telemetry & Biometric Infrastructure • <strong>{todayFormatted}</strong>
          </Typography>
        </Box>

        <Stack direction="row" spacing={1.5}>
          <Button
            variant="outlined"
            color="primary"
            startIcon={<PersonAddOutlinedIcon />}
            onClick={() => setDrawerOpen(true)}
          >
            Add Employee
          </Button>

          <Button
            variant="contained"
            color="primary"
            startIcon={<FlashOnIcon />}
            onClick={() => setEodDialogOpen(true)}
            sx={{ bgcolor: '#4338CA' }}
          >
            Finalize Day (EOD)
          </Button>
        </Stack>
      </Box>

      {/* Success Notification on EOD */}
      {eodSuccessBanner && (
        <Card sx={{ mb: 3, bgcolor: '#ECFDF5', border: '1px solid #A7F3D0', p: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
              <CheckCircleOutlineIcon sx={{ color: '#059669' }} />
              <Typography variant="body2" sx={{ fontWeight: 600, color: '#065F46' }}>
                {eodMessage || 'End-of-Day attendance finalization completed successfully. All active shifts calculated.'}
              </Typography>
            </Box>
            <Button size="small" sx={{ color: '#065F46', fontWeight: 700 }} onClick={() => setEodSuccessBanner(false)}>
              Dismiss
            </Button>
          </Box>
        </Card>
      )}

      {/* KPI Cards Grid */}
      <Grid container spacing={2.5} sx={{ mb: 3.5 }}>
        <Grid item xs={12} sm={6} lg={3}>
          <MetricCard
            title="Total Active Roster"
            value={totalEmployees}
            subtitle="Registered employees"
            icon={<PeopleAltOutlinedIcon />}
            accentColor="#4338CA"
          />
        </Grid>

        <Grid item xs={12} sm={6} lg={3}>
          <MetricCard
            title="Present Today"
            value={presentCount + inProgressCount}
            subtitle={`${inProgressCount} currently checked in`}
            trend={{ value: `${(((presentCount + inProgressCount) / totalEmployees) * 100).toFixed(1)}% attendance`, positive: true }}
            icon={<CheckCircleOutlineIcon />}
            accentColor="#10B981"
          />
        </Grid>

        <Grid item xs={12} sm={6} lg={3}>
          <MetricCard
            title="Half-Day Shifts"
            value={halfDayCount}
            subtitle="< 9 hrs worked duration"
            icon={<HourglassEmptyIcon />}
            accentColor="#F59E0B"
          />
        </Grid>

        <Grid item xs={12} sm={6} lg={3}>
          <MetricCard
            title="Absent / Unlogged"
            value={absentCount}
            subtitle="No scanner verification"
            trend={{ value: 'Pending EOD' }}
            icon={<HighlightOffIcon />}
            accentColor="#EF4444"
          />
        </Grid>
      </Grid>

      {/* Main Live Activity Table */}
      <Card sx={{ p: 1, borderRadius: 3 }}>
        <CardContent sx={{ p: 2 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Box>
              <Typography variant="h5" sx={{ fontWeight: 700, color: '#0F172A' }}>
                Today's Live Attendance Stream
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Real-time edge camera check-in and check-out logs
              </Typography>
            </Box>

            <Button
              size="small"
              variant="outlined"
              endIcon={<FactCheckOutlinedIcon fontSize="small" />}
              onClick={() => navigate('/attendance')}
            >
              View Full Matrix
            </Button>
          </Box>

          <TableContainer component={Paper} variant="outlined" sx={{ borderRadius: 2 }}>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Employee</TableCell>
                  <TableCell>Employee ID</TableCell>
                  <TableCell>First Check-In</TableCell>
                  <TableCell>Latest Check-Out</TableCell>
                  <TableCell>Hours</TableCell>
                  <TableCell>Status</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {attendanceRecords.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={6} sx={{ py: 6, textAlign: 'center' }}>
                      <Typography variant="body2" color="text.secondary">
                        No attendance activity logged for today yet.
                      </Typography>
                    </TableCell>
                  </TableRow>
                ) : (
                  attendanceRecords.map((rec) => (
                    <TableRow key={rec.employee_id} hover sx={{ cursor: 'pointer' }} onClick={() => navigate(`/employees/${rec.employee_id}`)}>
                      <TableCell>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
                          <Avatar sx={{ width: 32, height: 32, bgcolor: '#4338CA', fontSize: '0.75rem', fontWeight: 700 }}>
                            {rec.name.slice(0, 2).toUpperCase()}
                          </Avatar>
                          <Typography variant="body2" sx={{ fontWeight: 600 }}>
                            {rec.name}
                          </Typography>
                        </Box>
                      </TableCell>

                      <TableCell>
                        <Typography variant="body2" sx={{ fontFamily: 'monospace', fontWeight: 600 }}>
                          {rec.employee_id}
                        </Typography>
                      </TableCell>

                      <TableCell>
                        <Typography variant="body2" sx={{ fontFamily: 'monospace', color: rec.check_in ? '#0F172A' : '#94A3B8' }}>
                          {rec.check_in || '—'}
                        </Typography>
                      </TableCell>

                      <TableCell>
                        <Typography variant="body2" sx={{ fontFamily: 'monospace', color: rec.check_out ? '#0F172A' : '#94A3B8' }}>
                          {rec.check_out || '—'}
                        </Typography>
                      </TableCell>

                      <TableCell>
                        <Typography variant="body2" sx={{ fontFamily: 'monospace', fontWeight: 600 }}>
                          {rec.working_hours ? `${rec.working_hours.toFixed(2)}h` : '—'}
                        </Typography>
                      </TableCell>

                      <TableCell>
                        <StatusChip status={rec.status} />
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </TableContainer>
        </CardContent>
      </Card>

      {/* Slide-in Employee Drawer */}
      <EmployeeDrawer
        open={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        onSubmit={handleAddEmployee}
      />

      {/* End of Day Finalization Confirmation Dialog */}
      <ConfirmDialog
        open={eodDialogOpen}
        title="Trigger Manual End-of-Day Finalization?"
        description="This will evaluate all active shifts for today, finalize all in-progress records, and mark employees with no scanner verifications as Absent. This action writes permanent audit records."
        confirmLabel="Finalize Day Now"
        confirmColor="primary"
        loading={eodLoading}
        onConfirm={handleEODConfirm}
        onCancel={() => setEodDialogOpen(false)}
      />
    </Box>
  );
};
