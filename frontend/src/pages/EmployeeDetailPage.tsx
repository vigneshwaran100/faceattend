import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Box,
  Typography,
  Button,
  Grid,
  Card,
  CardContent,
  Avatar,
  Stack,
  TextField,
  Divider,
  Switch,
  FormControlLabel,
  Alert,
} from '@mui/material';
import {
  ArrowBack as ArrowBackIcon,
  EditOutlined as EditOutlinedIcon,
  Save as SaveOutlinedIcon,
  CloseOutlined as CloseOutlinedIcon,
  CameraAltOutlined as CameraAltOutlinedIcon,
  CheckCircle as CheckCircleIcon,
} from '@mui/icons-material';
import { StatusChip } from '../components/common/StatusChip';
import { AttendanceSummaryCards } from '../components/attendance/AttendanceSummaryCards';
import { AttendanceTable } from '../components/attendance/AttendanceTable';
import { ConfirmDialog } from '../components/common/ConfirmDialog';
import { LoadingSkeleton } from '../components/common/LoadingSkeleton';
import { ErrorAlert } from '../components/common/ErrorAlert';
import { employeeService } from '../services/employeeService';
import { EmployeeResponse, AttendanceSummaryResponse, AttendanceRecordResponse } from '../types/api';

export const EmployeeDetailPage: React.FC = () => {
  const { employeeId } = useParams<{ employeeId: string }>();
  const navigate = useNavigate();

  const [isEditing, setIsEditing] = useState(false);
  const [statusConfirmOpen, setStatusConfirmOpen] = useState(false);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [employee, setEmployee] = useState<EmployeeResponse | null>(null);
  const [summary, setSummary] = useState<AttendanceSummaryResponse | null>(null);
  const [historyRecords, setHistoryRecords] = useState<AttendanceRecordResponse[]>([]);

  // Edit form state
  const [editName, setEditName] = useState('');
  const [editEmail, setEditEmail] = useState('');
  const [editDept, setEditDept] = useState('');
  const [editTeam, setEditTeam] = useState('');
  const [editDesignation, setEditDesignation] = useState('');

  const fetchEmployeeData = async () => {
    if (!employeeId) return;
    setLoading(true);
    setError(null);
    try {
      const emp = await employeeService.getEmployee(employeeId);
      setEmployee(emp);
      setEditName(emp.name);
      setEditEmail(emp.email);
      setEditDept(emp.department_id || '');
      setEditTeam(emp.team_id || '');
      setEditDesignation(emp.designation || '');

      // Load attendance summary and history
      try {
        const sum = await employeeService.getAttendanceSummary(employeeId);
        setSummary(sum);
      } catch {
        // Fallback default summary if no punches recorded yet
        setSummary({
          employee_id: employeeId,
          start_date: null,
          end_date: null,
          total_records: 0,
          total_working_days: 0,
          present_days: 0,
          half_days: 0,
          incomplete_days: 0,
          absent_days: 0,
          in_progress_days: 0,
          total_working_hours: 0,
          attendance_percentage: 100,
        });
      }

      try {
        const hist = await employeeService.getAttendanceHistory(employeeId);
        setHistoryRecords(hist.attendance || []);
      } catch {
        setHistoryRecords([]);
      }
    } catch (err: any) {
      setError(err.message || `Failed to retrieve employee ${employeeId}.`);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchEmployeeData();
  }, [employeeId]);

  const handleSaveEdit = async () => {
    if (!employeeId || !employee) return;
    try {
      const updated = await employeeService.updateEmployee(employeeId, {
        name: editName,
        email: editEmail,
        department_id: editDept || null,
        team_id: editTeam || null,
        designation: editDesignation || null,
        status: employee.status,
      });
      setEmployee(updated);
      setIsEditing(false);
      setSuccessMessage('Employee profile details updated successfully.');
      setTimeout(() => setSuccessMessage(null), 4000);
    } catch (err: any) {
      setError(err.message || 'Failed to update employee profile.');
    }
  };

  const handleToggleStatus = async () => {
    if (!employeeId || !employee) return;
    const newStatus = employee.status === 'active' ? 'inactive' : 'active';
    try {
      const updated = await employeeService.updateStatus(employeeId, newStatus);
      setEmployee(updated);
      setStatusConfirmOpen(false);
      setSuccessMessage(`Employee status changed to ${newStatus.toUpperCase()}.`);
      setTimeout(() => setSuccessMessage(null), 4000);
    } catch (err: any) {
      setError(err.message || 'Failed to update status.');
      setStatusConfirmOpen(false);
    }
  };

  if (loading && !employee) {
    return <LoadingSkeleton />;
  }

  if (!employee) {
    return (
      <Box sx={{ p: 3 }}>
        <ErrorAlert
          title="Employee Profile"
          message={error || `Employee ${employeeId} not found.`}
          onRetry={fetchEmployeeData}
        />
      </Box>
    );
  }

  return (
    <Box>
      {/* Top Back Nav & Actions */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Button
          variant="text"
          color="secondary"
          startIcon={<ArrowBackIcon />}
          onClick={() => navigate('/employees')}
          sx={{ fontWeight: 600 }}
        >
          Back to Directory
        </Button>

        <Stack direction="row" spacing={1.5}>
          {isEditing ? (
            <>
              <Button
                variant="outlined"
                color="secondary"
                startIcon={<CloseOutlinedIcon />}
                onClick={() => setIsEditing(false)}
              >
                Cancel
              </Button>
              <Button
                variant="contained"
                color="primary"
                startIcon={<SaveOutlinedIcon />}
                onClick={handleSaveEdit}
              >
                Save Changes
              </Button>
            </>
          ) : (
            <Button
              variant="outlined"
              color="primary"
              startIcon={<EditOutlinedIcon />}
              onClick={() => setIsEditing(true)}
            >
              Edit Profile
            </Button>
          )}
        </Stack>
      </Box>

      {successMessage && (
        <Alert severity="success" sx={{ mb: 3 }}>
          {successMessage}
        </Alert>
      )}

      {/* Main Profile Header Card */}
      <Card sx={{ p: 1, mb: 3.5, borderRadius: 3 }}>
        <CardContent sx={{ p: 3 }}>
          <Grid container spacing={3} alignItems="center">
            <Grid item xs={12} md={8}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2.5 }}>
                <Avatar
                  sx={{
                    width: 72,
                    height: 72,
                    bgcolor: '#4338CA',
                    fontSize: '1.75rem',
                    fontWeight: 700,
                    boxShadow: '0 4px 12px rgba(67, 56, 202, 0.25)',
                  }}
                >
                  {employee.name.slice(0, 2).toUpperCase()}
                </Avatar>

                <Box sx={{ flex: 1 }}>
                  {isEditing ? (
                    <Stack spacing={1.5} sx={{ maxWidth: 400 }}>
                      <TextField
                        size="small"
                        label="Full Name"
                        value={editName}
                        onChange={(e) => setEditName(e.target.value)}
                      />
                      <TextField
                        size="small"
                        label="Work Email"
                        value={editEmail}
                        onChange={(e) => setEditEmail(e.target.value)}
                      />
                    </Stack>
                  ) : (
                    <>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 0.5 }}>
                        <Typography variant="h3" sx={{ fontWeight: 800 }}>
                          {employee.name}
                        </Typography>
                        <StatusChip status={employee.status} />
                      </Box>
                      <Typography variant="body2" color="text.secondary" sx={{ fontFamily: 'monospace' }}>
                        {employee.employee_id} • {employee.email}
                      </Typography>
                    </>
                  )}
                </Box>
              </Box>
            </Grid>

            <Grid item xs={12} md={4}>
              <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: { xs: 'flex-start', md: 'flex-end' }, gap: 1.5 }}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={employee.status === 'active'}
                      onChange={() => setStatusConfirmOpen(true)}
                      color="success"
                    />
                  }
                  label={
                    <Typography variant="body2" sx={{ fontWeight: 600 }}>
                      Account: {employee.status.toUpperCase()}
                    </Typography>
                  }
                />
                <Typography variant="caption" color="text.secondary">
                  Member since {new Date(employee.created_at).toLocaleDateString()}
                </Typography>
              </Box>
            </Grid>
          </Grid>

          <Divider sx={{ my: 3 }} />

          {/* Department, Team & Biometric Status Grid */}
          <Grid container spacing={3}>
            <Grid item xs={12} sm={4}>
              <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 600, textTransform: 'uppercase' }}>
                Department
              </Typography>
              {isEditing ? (
                <TextField
                  size="small"
                  fullWidth
                  value={editDept}
                  onChange={(e) => setEditDept(e.target.value)}
                  sx={{ mt: 0.5 }}
                />
              ) : (
                <Typography variant="body1" sx={{ fontWeight: 600, mt: 0.5 }}>
                  {employee.department_id || 'Not Assigned'}
                </Typography>
              )}
            </Grid>

            <Grid item xs={12} sm={4}>
              <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 600, textTransform: 'uppercase' }}>
                Team Assignment
              </Typography>
              {isEditing ? (
                <TextField
                  size="small"
                  fullWidth
                  value={editTeam}
                  onChange={(e) => setEditTeam(e.target.value)}
                  sx={{ mt: 0.5 }}
                />
              ) : (
                <Typography variant="body1" sx={{ fontWeight: 600, mt: 0.5 }}>
                  {employee.team_id || 'Unassigned'}
                </Typography>
              )}
            </Grid>

            <Grid item xs={12} sm={4}>
              <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 600, textTransform: 'uppercase' }}>
                Job Designation
              </Typography>
              {isEditing ? (
                <TextField
                  size="small"
                  fullWidth
                  value={editDesignation}
                  onChange={(e) => setEditDesignation(e.target.value)}
                  sx={{ mt: 0.5 }}
                />
              ) : (
                <Typography variant="body1" sx={{ fontWeight: 600, mt: 0.5 }}>
                  {employee.designation || 'Staff'}
                </Typography>
              )}
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Biometric Face Profile CTA Card */}
      <Card sx={{ p: 2.5, mb: 3.5, borderRadius: 3, bgcolor: '#FFFFFF', border: '1px solid #E2E8F0' }}>
        <Box sx={{ display: 'flex', flexDirection: { xs: 'column', sm: 'row' }, justifyContent: 'space-between', alignItems: { xs: 'flex-start', sm: 'center' }, gap: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <Box
              sx={{
                width: 48,
                height: 48,
                borderRadius: 2.5,
                bgcolor: '#ECFDF5',
                color: '#059669',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <CheckCircleIcon />
            </Box>
            <Box>
              <Typography variant="h6" sx={{ fontWeight: 700 }}>
                Biometric Face Profile
              </Typography>
              <Typography variant="caption" color="text.secondary">
                10-Sample Multi-Pose Vector Embeddings stored in Milvus cluster
              </Typography>
            </Box>
          </Box>

          <Button
            variant="contained"
            color="primary"
            startIcon={<CameraAltOutlinedIcon />}
            onClick={() => navigate(`/enroll/${employee.employee_id}`)}
            disabled={employee.status !== 'active'}
          >
            Launch Face Studio
          </Button>
        </Box>
      </Card>

      {/* Monthly Attendance Summary Telemetry */}
      {summary && (
        <Box sx={{ mb: 3.5 }}>
          <Typography variant="h5" sx={{ fontWeight: 700, mb: 2 }}>
            Monthly Attendance Telemetry Summary
          </Typography>
          <AttendanceSummaryCards summary={summary as any} />
        </Box>
      )}

      {/* Recent Attendance Logs Table */}
      <Box>
        <Typography variant="h5" sx={{ fontWeight: 700, mb: 2 }}>
          Recent Timecard Verification History
        </Typography>
        <AttendanceTable
          records={historyRecords.map((r) => ({
            employee_id: r.employee_id,
            name: employee.name,
            check_in: r.check_in,
            check_out: r.check_out,
            working_hours: r.working_hours,
            status: r.status,
          }))}
        />
      </Box>

      {/* Account Status Toggle Confirmation Dialog */}
      <ConfirmDialog
        open={statusConfirmOpen}
        title={employee.status === 'active' ? 'Deactivate Employee Account?' : 'Reactivate Employee Account?'}
        description={
          employee.status === 'active'
            ? 'Deactivating this employee will immediately block them from biometric scanner check-in and checkout kiosks.'
            : 'Reactivating this employee will restore their biometric access credentials across all scanner kiosks.'
        }
        confirmLabel={employee.status === 'active' ? 'Deactivate' : 'Reactivate'}
        confirmColor={employee.status === 'active' ? 'error' : 'primary'}
        onConfirm={handleToggleStatus}
        onCancel={() => setStatusConfirmOpen(false)}
      />
    </Box>
  );
};
