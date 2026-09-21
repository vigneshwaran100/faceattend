import React from 'react';
import { Grid, Card, CardContent, Typography, Box, Chip } from '@mui/material';
import {
  BusinessOutlined as BusinessOutlinedIcon,
  GroupsOutlined as GroupsOutlinedIcon,
} from '@mui/icons-material';
import { Department, Team } from '../../services/types';
import { EmptyState } from '../common/EmptyState';

export const DepartmentList: React.FC<{ departments: Department[]; onCreateNew?: () => void }> = ({
  departments,
  onCreateNew,
}) => {
  if (departments.length === 0) {
    return (
      <EmptyState
        title="No Departments Configured"
        description="No organizational departments found. Create your first department to assign teams and employees."
        actionLabel="Create Department"
        onAction={onCreateNew}
      />
    );
  }

  return (
    <Grid container spacing={2.5}>
      {departments.map((dept) => (
        <Grid item xs={12} sm={6} md={4} key={dept.department_id}>
          <Card sx={{ height: '100%', p: 1 }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', mb: 2 }}>
                <Box
                  sx={{
                    width: 42,
                    height: 42,
                    borderRadius: 2.5,
                    backgroundColor: '#EEF2FF',
                    color: '#4338CA',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                  }}
                >
                  <BusinessOutlinedIcon />
                </Box>
                <Chip
                  size="small"
                  label={dept.department_id}
                  sx={{ fontFamily: 'monospace', fontWeight: 700, bgcolor: '#F1F5F9' }}
                />
              </Box>

              <Typography variant="h6" sx={{ fontWeight: 700, color: '#0F172A', mb: 0.5 }}>
                {dept.department_name}
              </Typography>

              <Typography variant="caption" color="text.secondary">
                Registered on {new Date(dept.created_at).toLocaleDateString()}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      ))}
    </Grid>
  );
};

export const TeamList: React.FC<{ teams: Team[]; onCreateNew?: () => void }> = ({
  teams,
  onCreateNew,
}) => {
  if (teams.length === 0) {
    return (
      <EmptyState
        title="No Teams Configured"
        description="No teams found. Create your first team to organize employee squads."
        actionLabel="Create Team"
        onAction={onCreateNew}
      />
    );
  }

  return (
    <Grid container spacing={2.5}>
      {teams.map((team) => (
        <Grid item xs={12} sm={6} md={4} key={team.team_id}>
          <Card sx={{ height: '100%', p: 1 }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', mb: 2 }}>
                <Box
                  sx={{
                    width: 42,
                    height: 42,
                    borderRadius: 2.5,
                    backgroundColor: '#ECFDF5',
                    color: '#059669',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                  }}
                >
                  <GroupsOutlinedIcon />
                </Box>
                <Chip
                  size="small"
                  label={team.team_id}
                  sx={{ fontFamily: 'monospace', fontWeight: 700, bgcolor: '#F1F5F9' }}
                />
              </Box>

              <Typography variant="h6" sx={{ fontWeight: 700, color: '#0F172A', mb: 0.5 }}>
                {team.team_name}
              </Typography>

              <Typography variant="caption" color="text.secondary">
                Created on {new Date(team.created_at).toLocaleDateString()}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      ))}
    </Grid>
  );
};
