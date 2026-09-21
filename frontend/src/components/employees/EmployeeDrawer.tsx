import React, { useState } from 'react';
import {
  Drawer,
  Box,
  Typography,
  IconButton,
  TextField,
  Button,
  Stack,
  Alert,
  Divider,
} from '@mui/material';
import {
  Close as CloseIcon,
  PersonAddOutlined as PersonAddOutlinedIcon,
} from '@mui/icons-material';
import { EmployeeCreateRequest } from '../../types/api';
import { CircularProgress } from '@mui/material';

interface EmployeeDrawerProps {
  open: boolean;
  onClose: () => void;
  onSubmit: (employeeData: EmployeeCreateRequest) => Promise<void>;
}

export const EmployeeDrawer: React.FC<EmployeeDrawerProps> = ({
  open,
  onClose,
  onSubmit,
}) => {
  const [employeeId, setEmployeeId] = useState('');
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [departmentId, setDepartmentId] = useState('');
  const [teamId, setTeamId] = useState('');
  const [designation, setDesignation] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!employeeId.trim() || !name.trim() || !email.trim()) {
      setError('Employee ID, Name, and Email are required fields.');
      return;
    }

    setSubmitting(true);
    try {
      await onSubmit({
        employee_id: employeeId.trim(),
        name: name.trim(),
        email: email.trim(),
        department_id: departmentId.trim() || null,
        team_id: teamId.trim() || null,
        designation: designation.trim() || null,
      });

      // Reset fields
      setEmployeeId('');
      setName('');
      setEmail('');
      setDepartmentId('');
      setTeamId('');
      setDesignation('');
      onClose();
    } catch (err: any) {
      setError(err.message || 'Failed to register employee.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Drawer
      anchor="right"
      open={open}
      onClose={onClose}
      PaperProps={{
        sx: {
          width: { xs: '100%', sm: 440 },
          p: 0,
        },
      }}
    >
      <Box sx={{ p: 3, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
          <Box
            sx={{
              width: 36,
              height: 36,
              borderRadius: 2,
              backgroundColor: '#EEF2FF',
              color: '#4338CA',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <PersonAddOutlinedIcon fontSize="small" />
          </Box>
          <Typography variant="h5" sx={{ fontWeight: 700 }}>
            Add New Employee
          </Typography>
        </Box>
        <IconButton size="small" onClick={onClose}>
          <CloseIcon fontSize="small" />
        </IconButton>
      </Box>

      <Divider />

      <Box component="form" onSubmit={handleSubmit} sx={{ p: 3, flex: 1, overflowY: 'auto' }}>
        {error && (
          <Alert severity="error" sx={{ mb: 3 }}>
            {error}
          </Alert>
        )}

        <Stack spacing={2.5}>
          <TextField
            label="Employee ID"
            placeholder="e.g. EMP-1042"
            value={employeeId}
            onChange={(e) => setEmployeeId(e.target.value)}
            required
            fullWidth
            helperText="Unique enterprise identifier string"
          />

          <TextField
            label="Full Legal Name"
            placeholder="e.g. Alex Chen"
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
            fullWidth
          />

          <TextField
            label="Work Email Address"
            type="email"
            placeholder="e.g. alex.chen@enterprise.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            fullWidth
          />

          <TextField
            label="Department ID"
            placeholder="e.g. ENG"
            value={departmentId}
            onChange={(e) => setDepartmentId(e.target.value)}
            fullWidth
          />

          <TextField
            label="Team ID"
            placeholder="e.g. CORE-AI"
            value={teamId}
            onChange={(e) => setTeamId(e.target.value)}
            fullWidth
          />

          <TextField
            label="Job Designation"
            placeholder="e.g. Senior Machine Learning Engineer"
            value={designation}
            onChange={(e) => setDesignation(e.target.value)}
            fullWidth
          />
        </Stack>

        <Box sx={{ mt: 4, display: 'flex', gap: 2, justifyContent: 'flex-end' }}>
          <Button variant="outlined" onClick={onClose} disabled={submitting}>
            Cancel
          </Button>
          <Button type="submit" variant="contained" color="primary" disabled={submitting}>
            {submitting ? <CircularProgress size={20} color="inherit" /> : 'Register Employee'}
          </Button>
        </Box>
      </Box>
    </Drawer>
  );
};
