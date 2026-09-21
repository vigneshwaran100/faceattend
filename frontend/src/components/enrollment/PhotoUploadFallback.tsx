import React, { useState } from 'react';
import { Box, Typography, Button, Paper, Alert } from '@mui/material';
import {
  CloudUploadOutlined as CloudUploadOutlinedIcon,
  CheckCircleOutline as CheckCircleOutlineIcon,
} from '@mui/icons-material';

interface PhotoUploadFallbackProps {
  onFileSelect: (file: File) => void;
  onSwitchToCamera?: () => void;
}

export const PhotoUploadFallback: React.FC<PhotoUploadFallbackProps> = ({
  onFileSelect,
  onSwitchToCamera,
}) => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    setError(null);
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      if (!file.type.startsWith('image/')) {
        setError('Please upload an image file (JPEG, PNG).');
        return;
      }
      setSelectedFile(file);
      setPreviewUrl(URL.createObjectURL(file));
      onFileSelect(file);
    }
  };

  return (
    <Paper
      elevation={0}
      sx={{
        p: 4,
        border: '1px dashed #CBD5E1',
        borderRadius: 3,
        backgroundColor: '#FFFFFF',
        textAlign: 'center',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
      }}
    >
      <Box
        sx={{
          width: 56,
          height: 56,
          borderRadius: 3,
          backgroundColor: '#EEF2FF',
          color: '#4338CA',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          mb: 2,
        }}
      >
        <CloudUploadOutlinedIcon sx={{ fontSize: 32 }} />
      </Box>

      <Typography variant="h6" sx={{ fontWeight: 700, mb: 0.5 }}>
        Single Photo Face Enrollment Fallback
      </Typography>

      <Typography variant="body2" color="text.secondary" sx={{ maxWidth: 420, mb: 3 }}>
        Upload a high-resolution frontal headshot with clear lighting and a neutral background.
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 2, width: '100%', maxWidth: 400 }}>
          {error}
        </Alert>
      )}

      {previewUrl && selectedFile ? (
        <Box sx={{ mb: 3, textAlign: 'center' }}>
          <Box
            sx={{
              width: 140,
              height: 140,
              borderRadius: '50%',
              overflow: 'hidden',
              mx: 'auto',
              mb: 1.5,
              border: '3px solid #10B981',
            }}
          >
            <img src={previewUrl} alt="Selected face" style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
          </Box>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 1, color: '#065F46' }}>
            <CheckCircleOutlineIcon sx={{ fontSize: 18 }} />
            <Typography variant="body2" sx={{ fontWeight: 600 }}>
              {selectedFile.name} ({(selectedFile.size / 1024).toFixed(1)} KB)
            </Typography>
          </Box>
        </Box>
      ) : null}

      <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', justifyContent: 'center' }}>
        <Button
          variant="contained"
          component="label"
          startIcon={<CloudUploadOutlinedIcon />}
        >
          {selectedFile ? 'Choose Different Image' : 'Select Photo from Computer'}
          <input type="file" accept="image/*" hidden onChange={handleFileInput} />
        </Button>

        {onSwitchToCamera && (
          <Button variant="outlined" onClick={onSwitchToCamera}>
            Switch to Live Camera
          </Button>
        )}
      </Box>
    </Paper>
  );
};
