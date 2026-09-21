import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Typography,
  Button,
  TextField,
  InputAdornment,
  MenuItem,
  Stack,
  Card,
} from '@mui/material';
import {
  Search as SearchIcon,
  PersonAddOutlined as PersonAddOutlinedIcon,
} from '@mui/icons-material';
import { EmployeeTable } from '../components/employees/EmployeeTable';
import { EmployeeDrawer } from '../components/employees/EmployeeDrawer';
import { ErrorAlert } from '../components/common/ErrorAlert';
import { LoadingSkeleton } from '../components/common/LoadingSkeleton';
import { attendanceService } from '../services/attendanceService';
import { employeeService } from '../services/employeeService';
import { Employee } from '../services/types';
import { EmployeeCreateRequest } from '../types/api';

export const EmployeesPage: React.FC = () => {
  const navigate = useNavigate();
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [deptFilter, setDeptFilter] = useState('');

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [employees, setEmployees] = useState<Employee[]>([]);

  const fetchEmployees = async () => {
    setLoading(true);
    setError(null);
    try {
      // Backend provides active employee roster in daily report
      const report = await attendanceService.getDailyReport();
      const mapped: Employee[] = (report.records || []).map((r) => ({
        employee_id: r.employee_id,
        name: r.name,
        email: `${r.employee_id.toLowerCase()}@enterprise.com`,
        department_id: 'ENG',
        team_id: 'CORE',
        designation: 'Active Staff',
        status: 'active',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      }));
      setEmployees(mapped);
    } catch (err: any) {
      setError(err.message || 'Failed to load employee roster.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchEmployees();
  }, []);

  const handleAddEmployee = async (newEmpData: EmployeeCreateRequest) => {
    try {
      const created = await employeeService.createEmployee(newEmpData);
      setEmployees((prev) => [
        {
          employee_id: created.employee_id,
          name: created.name,
          email: created.email,
          department_id: created.department_id,
          team_id: created.team_id,
          designation: created.designation,
          status: (created.status as any) || 'active',
          created_at: created.created_at,
          updated_at: created.updated_at,
        },
        ...prev,
      ]);
    } catch (err: any) {
      throw err;
    }
  };

  const filteredEmployees = employees.filter((emp) => {
    const matchesQuery =
      emp.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      emp.employee_id.toLowerCase().includes(searchQuery.toLowerCase()) ||
      emp.email.toLowerCase().includes(searchQuery.toLowerCase());

    const matchesStatus = !statusFilter || emp.status === statusFilter;
    const matchesDept = !deptFilter || emp.department_id === deptFilter;

    return matchesQuery && matchesStatus && matchesDept;
  });

  if (loading && employees.length === 0) {
    return <LoadingSkeleton />;
  }

  return (
    <Box>
      {error && (
        <Box sx={{ mb: 3 }}>
          <ErrorAlert
            title="Workforce Directory Error"
            message={error}
            onRetry={fetchEmployees}
            onClose={() => setError(null)}
          />
        </Box>
      )}
      {/* Top Header */}
      <Box sx={{ display: 'flex', flexDirection: { xs: 'column', sm: 'row' }, justifyContent: 'space-between', alignItems: { xs: 'flex-start', sm: 'center' }, gap: 2, mb: 3.5 }}>
        <Box>
          <Typography variant="h2" sx={{ fontWeight: 800, color: '#0F172A', mb: 0.5 }}>
            Employee Workforce Directory
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Manage employee identities, status, and biometric enrollment profiles
          </Typography>
        </Box>

        <Button
          variant="contained"
          color="primary"
          startIcon={<PersonAddOutlinedIcon />}
          onClick={() => setDrawerOpen(true)}
        >
          Add New Employee
        </Button>
      </Box>

      {/* Filter and Search Bar */}
      <Card sx={{ p: 2.5, mb: 3, borderRadius: 3 }}>
        <Stack direction={{ xs: 'column', md: 'row' }} spacing={2} alignItems="center">
          <TextField
            fullWidth
            placeholder="Search employees by name, ID (e.g. EMP-1001), or email..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <SearchIcon sx={{ color: '#94A3B8' }} />
                </InputAdornment>
              ),
            }}
          />

          <TextField
            select
            label="Department"
            value={deptFilter}
            onChange={(e) => setDeptFilter(e.target.value)}
            sx={{ minWidth: 160 }}
          >
            <MenuItem value="">All Departments</MenuItem>
            <MenuItem value="ENG">Engineering (ENG)</MenuItem>
            <MenuItem value="OPS">Operations (OPS)</MenuItem>
            <MenuItem value="HR">Human Resources (HR)</MenuItem>
            <MenuItem value="PRODUCT">Product (PRODUCT)</MenuItem>
          </TextField>

          <TextField
            select
            label="Status"
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            sx={{ minWidth: 140 }}
          >
            <MenuItem value="">All Statuses</MenuItem>
            <MenuItem value="active">Active</MenuItem>
            <MenuItem value="inactive">Inactive</MenuItem>
          </TextField>
        </Stack>
      </Card>

      {/* Employee Data Table */}
      <EmployeeTable
        employees={filteredEmployees}
        onViewEmployee={(id) => navigate(`/employees/${id}`)}
        onEnrollFace={(id) => navigate(`/employees/${id}/enroll`)}
      />

      {/* Slide-in Registration Panel */}
      <EmployeeDrawer
        open={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        onSubmit={handleAddEmployee}
      />
    </Box>
  );
};
