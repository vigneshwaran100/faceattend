import React, { useState } from 'react';
import {
  Box,
  Typography,
  Button,
  Tabs,
  Tab,
  Card,
  Alert,
} from '@mui/material';
import {
  Add as AddIcon,
  BusinessOutlined as BusinessOutlinedIcon,
  GroupsOutlined as GroupsOutlinedIcon,
} from '@mui/icons-material';
import { DepartmentList, TeamList } from '../components/organization/DepartmentList';
import { CreateOrgDialog } from '../components/organization/CreateOrgDialog';
import { organizationService } from '../services/organizationService';
import { Department, Team } from '../services/types';

export const OrganizationPage: React.FC = () => {
  const [tabIndex, setTabIndex] = useState(0);
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [duplicateError, setDuplicateError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const [departments, setDepartments] = useState<Department[]>([
    {
      department_id: 'ENG',
      department_name: 'Engineering & Architecture',
      created_at: '2025-01-10T08:00:00Z',
      updated_at: '2025-01-10T08:00:00Z',
    },
    {
      department_id: 'OPS',
      department_name: 'Security & Operations',
      created_at: '2025-01-10T08:00:00Z',
      updated_at: '2025-01-10T08:00:00Z',
    },
    {
      department_id: 'HR',
      department_name: 'People Operations & HR',
      created_at: '2025-01-10T08:00:00Z',
      updated_at: '2025-01-10T08:00:00Z',
    },
    {
      department_id: 'PRODUCT',
      department_name: 'Product Experience',
      created_at: '2025-01-12T09:00:00Z',
      updated_at: '2025-01-12T09:00:00Z',
    },
  ]);

  const [teams, setTeams] = useState<Team[]>([
    {
      team_id: 'CORE-AI',
      team_name: 'Core Biometrics & AI',
      created_at: '2025-01-10T08:30:00Z',
      updated_at: '2025-01-10T08:30:00Z',
    },
    {
      team_id: 'VISION',
      team_name: 'Computer Vision Squad',
      created_at: '2025-01-10T08:30:00Z',
      updated_at: '2025-01-10T08:30:00Z',
    },
    {
      team_id: 'SECOPS',
      team_name: 'SecOps & Hardware Infrastructure',
      created_at: '2025-01-10T08:30:00Z',
      updated_at: '2025-01-10T08:30:00Z',
    },
    {
      team_id: 'PEOPLE-OPS',
      team_name: 'Talent & Workplace Management',
      created_at: '2025-01-10T08:30:00Z',
      updated_at: '2025-01-10T08:30:00Z',
    },
  ]);

  const handleCreateOrg = async (id: string, name: string) => {
    setDuplicateError(null);

    try {
      if (tabIndex === 0) {
        const created = await organizationService.createDepartment({
          department_id: id.trim().toUpperCase(),
          department_name: name.trim(),
        });
        setDepartments((prev) => [
          {
            department_id: created.department_id,
            department_name: created.department_name,
            created_at: created.created_at,
            updated_at: created.updated_at,
          },
          ...prev,
        ]);
        setSuccessMessage(`Department '${created.department_name}' created successfully.`);
      } else {
        const created = await organizationService.createTeam({
          team_id: id.trim().toUpperCase(),
          team_name: name.trim(),
        });
        setTeams((prev) => [
          {
            team_id: created.team_id,
            team_name: created.team_name,
            created_at: created.created_at,
            updated_at: created.updated_at,
          },
          ...prev,
        ]);
        setSuccessMessage(`Team '${created.team_name}' created successfully.`);
      }

      setCreateDialogOpen(false);
      setTimeout(() => setSuccessMessage(null), 4000);
    } catch (err: any) {
      setDuplicateError(err.message || 'Failed to create organization unit.');
    }
  };

  return (
    <Box>
      {/* Top Header */}
      <Box sx={{ display: 'flex', flexDirection: { xs: 'column', sm: 'row' }, justifyContent: 'space-between', alignItems: { xs: 'flex-start', sm: 'center' }, gap: 2, mb: 3.5 }}>
        <Box>
          <Typography variant="h2" sx={{ fontWeight: 800, color: '#0F172A', mb: 0.5 }}>
            Organizational Structure
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Manage company departments, team squads, and workforce groupings
          </Typography>
        </Box>

        <Button
          variant="contained"
          color="primary"
          startIcon={<AddIcon />}
          onClick={() => {
            setDuplicateError(null);
            setCreateDialogOpen(true);
          }}
        >
          {tabIndex === 0 ? 'Create Department' : 'Create Team'}
        </Button>
      </Box>

      {successMessage && (
        <Alert severity="success" sx={{ mb: 3 }}>
          {successMessage}
        </Alert>
      )}

      {/* Tabs Switcher */}
      <Card sx={{ mb: 3.5, borderRadius: 3 }}>
        <Tabs
          value={tabIndex}
          onChange={(_, newVal) => setTabIndex(newVal)}
          sx={{ px: 2, borderBottom: '1px solid #E2E8F0' }}
        >
          <Tab
            icon={<BusinessOutlinedIcon fontSize="small" />}
            iconPosition="start"
            label={`Departments (${departments.length})`}
            sx={{ fontWeight: 700 }}
          />
          <Tab
            icon={<GroupsOutlinedIcon fontSize="small" />}
            iconPosition="start"
            label={`Teams (${teams.length})`}
            sx={{ fontWeight: 700 }}
          />
        </Tabs>
      </Card>

      {/* Tab Panels */}
      {tabIndex === 0 ? (
        <DepartmentList
          departments={departments}
          onCreateNew={() => setCreateDialogOpen(true)}
        />
      ) : (
        <TeamList
          teams={teams}
          onCreateNew={() => setCreateDialogOpen(true)}
        />
      )}

      {/* Create Dialog */}
      <CreateOrgDialog
        open={createDialogOpen}
        type={tabIndex === 0 ? 'department' : 'team'}
        duplicateError={duplicateError}
        onClose={() => {
          setDuplicateError(null);
          setCreateDialogOpen(false);
        }}
        onSubmit={handleCreateOrg}
      />
    </Box>
  );
};
