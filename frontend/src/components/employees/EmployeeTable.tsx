import React from 'react';
import {
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Box,
  Avatar,
  Typography,
  IconButton,
  Tooltip,
} from '@mui/material';
import {
  VisibilityOutlined as VisibilityOutlinedIcon,
  CameraAltOutlined as CameraAltOutlinedIcon,
} from '@mui/icons-material';
import { Employee } from '../../services/types';
import { StatusChip } from '../common/StatusChip';
import { EmptyState } from '../common/EmptyState';

interface EmployeeTableProps {
  employees: Employee[];
  onViewEmployee: (employeeId: string) => void;
  onEnrollFace: (employeeId: string) => void;
}

export const EmployeeTable: React.FC<EmployeeTableProps> = ({
  employees,
  onViewEmployee,
  onEnrollFace,
}) => {
  if (employees.length === 0) {
    return (
      <EmptyState
        title="No Employees Found"
        description="No employee records match your search criteria. Add a new employee or clear filters."
      />
    );
  }

  return (
    <TableContainer component={Paper} variant="outlined" sx={{ borderRadius: 3 }}>
      <Table sx={{ minWidth: 750 }}>
        <TableHead>
          <TableRow>
            <TableCell>Employee</TableCell>
            <TableCell>Employee ID</TableCell>
            <TableCell>Department & Team</TableCell>
            <TableCell>Designation</TableCell>
            <TableCell>Account Status</TableCell>
            <TableCell align="right">Actions</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {employees.map((emp) => (
            <TableRow key={emp.employee_id} hover sx={{ cursor: 'pointer' }} onClick={() => onViewEmployee(emp.employee_id)}>
              <TableCell>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
                  <Avatar
                    sx={{
                      width: 38,
                      height: 38,
                      bgcolor: '#4338CA',
                      fontSize: '0.875rem',
                      fontWeight: 600,
                    }}
                  >
                    {emp.name.slice(0, 2).toUpperCase()}
                  </Avatar>
                  <Box>
                    <Typography variant="body2" sx={{ fontWeight: 600, color: '#0F172A' }}>
                      {emp.name}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      {emp.email}
                    </Typography>
                  </Box>
                </Box>
              </TableCell>

              <TableCell>
                <Typography variant="body2" sx={{ fontFamily: 'monospace', fontWeight: 600 }}>
                  {emp.employee_id}
                </Typography>
              </TableCell>

              <TableCell>
                <Typography variant="body2" sx={{ fontWeight: 500 }}>
                  {emp.department_id || 'General'}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  {emp.team_id ? `Team: ${emp.team_id}` : 'Unassigned'}
                </Typography>
              </TableCell>

              <TableCell>
                <Typography variant="body2" color="text.secondary">
                  {emp.designation || 'Staff'}
                </Typography>
              </TableCell>

              <TableCell>
                <StatusChip status={emp.status} />
              </TableCell>

              <TableCell align="right" onClick={(e) => e.stopPropagation()}>
                <Box sx={{ display: 'flex', justifyContent: 'flex-end', gap: 1 }}>
                  <Tooltip title="View Profile">
                    <IconButton
                      size="small"
                      color="primary"
                      onClick={() => onViewEmployee(emp.employee_id)}
                    >
                      <VisibilityOutlinedIcon fontSize="small" />
                    </IconButton>
                  </Tooltip>

                  <Tooltip title="Face Biometric Studio">
                    <IconButton
                      size="small"
                      sx={{ color: '#059669' }}
                      onClick={() => onEnrollFace(emp.employee_id)}
                      disabled={emp.status !== 'active'}
                    >
                      <CameraAltOutlinedIcon fontSize="small" />
                    </IconButton>
                  </Tooltip>
                </Box>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  );
};
