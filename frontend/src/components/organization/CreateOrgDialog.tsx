import React, { useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Button,
  Stack,
  Alert,
  Typography,
  Box,
} from '@mui/material';
import {
  BusinessOutlined as BusinessOutlinedIcon,
  GroupsOutlined as GroupsOutlinedIcon,
} from '@mui/icons-material';

interface CreateOrgDialogProps {
  open: boolean;
  type: 'department' | 'team';
  onClose: () => void;
  onSubmit: (id: string, name: string) => void;
  duplicateError?: string | null;
}

export const CreateOrgDialog: React.FC<CreateOrgDialogProps> = ({
  open,
  type,
  onClose,
  onSubmit,
  duplicateError,
}) => {
  const [id, setId] = useState('');
  const [name, setName] = useState('');
  const [localError, setLocalError] = useState<string | null>(null);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setLocalError(null);

    if (!id.trim() || !name.trim()) {
      setLocalError('Both ID and Name are required fields.');
      return;
    }

    onSubmit(id.trim(), name.trim());
  };

  const handleClose = () => {
    setId('');
    setName('');
    setLocalError(null);
    onClose();
  };

  const isDept = type === 'department';

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="xs" fullWidth>
      <Box component="form" onSubmit={handleSubmit}>
        <DialogTitle sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
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
            {isDept ? <BusinessOutlinedIcon fontSize="small" /> : <GroupsOutlinedIcon fontSize="small" />}
          </Box>
          <Typography variant="h5" sx={{ fontWeight: 700 }}>
            {isDept ? 'Create New Department' : 'Create New Team'}
          </Typography>
        </DialogTitle>

        <DialogContent>
          {(duplicateError || localError) && (
            <Alert severity="error" sx={{ mb: 2.5 }}>
              {duplicateError || localError}
            </Alert>
          )}

          <Stack spacing={2.5} sx={{ mt: 1 }}>
            <TextField
              label={isDept ? 'Department ID' : 'Team ID'}
              placeholder={isDept ? 'e.g. ENG' : 'e.g. CORE-AI'}
              value={id}
              onChange={(e) => setId(e.target.value)}
              required
              fullWidth
              helperText="Unique uppercase identifier string"
            />

            <TextField
              label={isDept ? 'Department Name' : 'Team Name'}
              placeholder={isDept ? 'e.g. Engineering & Architecture' : 'e.g. Computer Vision Squad'}
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
              fullWidth
            />
          </Stack>
        </DialogContent>

        <DialogActions sx={{ px: 3, pb: 3, pt: 1, gap: 1 }}>
          <Button variant="outlined" onClick={handleClose}>
            Cancel
          </Button>
          <Button type="submit" variant="contained" color="primary">
            {isDept ? 'Create Department' : 'Create Team'}
          </Button>
        </DialogActions>
      </Box>
    </Dialog>
  );
};
