import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Card,
  CardContent,
  Typography,
  TextField,
  Button,
  IconButton,
  InputAdornment,
  CircularProgress,
  Stack,
} from '@mui/material';
import {
  Visibility,
  VisibilityOff,
  LockOutlined as LockOutlinedIcon,
  PersonOutlineOutlined as PersonOutlineOutlinedIcon,
  ShieldOutlined as ShieldOutlinedIcon,
  ArrowForward as ArrowForwardIcon,
} from '@mui/icons-material';
import { authService } from '../services/authService';
import { ErrorAlert } from '../components/common/ErrorAlert';

export const LoginPage: React.FC = () => {
  const navigate = useNavigate();
  const [username, setUsername] = useState('admin');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!username.trim() || !password.trim()) {
      setError('Please provide username and password.');
      return;
    }

    setError(null);
    setLoading(true);

    try {
      await authService.login({
        username: username.trim(),
        password: password.trim(),
      });
      navigate('/dashboard');
    } catch (err: any) {
      setError(err.message || 'Authentication failed. Please verify credentials.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box sx={{ width: '100%', maxWidth: 440, mx: 'auto' }}>
      {/* Brand Header */}
      <Box sx={{ textAlign: 'center', mb: 4 }}>
        <Box
          sx={{
            width: 48,
            height: 48,
            borderRadius: 3,
            bgcolor: 'rgba(99, 102, 241, 0.2)',
            border: '1px solid rgba(99, 102, 241, 0.4)',
            color: '#818CF8',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            mx: 'auto',
            mb: 2,
            boxShadow: '0 0 24px rgba(99, 102, 241, 0.3)',
          }}
        >
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M3 7V5a2 2 0 0 1 2-2h2" />
            <path d="M17 3h2a2 2 0 0 1 2 2v2" />
            <path d="M21 17v2a2 2 0 0 1-2 2h-2" />
            <path d="M7 21H5a2 2 0 0 1-2-2v-2" />
            <circle cx="12" cy="11" r="3" />
            <path d="M9 16c.8 1.2 2 2 3 2s2.2-.8 3-2" />
          </svg>
        </Box>

        <Typography variant="h4" sx={{ fontWeight: 800, color: '#FFFFFF', letterSpacing: '-0.02em', mb: 0.5 }}>
          Face<span style={{ color: '#818CF8' }}>Attend</span>
        </Typography>
        <Typography variant="overline" sx={{ color: '#94A3B8', letterSpacing: '0.1em' }}>
          Enterprise Biometric Access Control
        </Typography>
      </Box>

      {/* Glassmorphic Login Card */}
      <Card
        sx={{
          bgcolor: 'rgba(17, 24, 39, 0.75)',
          backdropFilter: 'blur(16px)',
          border: '1px solid rgba(99, 102, 241, 0.28)',
          boxShadow: '0 20px 45px -10px rgba(0, 0, 0, 0.75), 0 0 25px -5px rgba(99, 102, 241, 0.15)',
          borderRadius: 4,
          p: 2,
        }}
      >
        <CardContent sx={{ p: 2 }}>
          <Typography variant="h5" sx={{ fontWeight: 700, color: '#F8FAFC', mb: 0.5 }}>
            Operator Sign In
          </Typography>
          <Typography variant="body2" sx={{ color: '#94A3B8', mb: 3 }}>
            Authenticate with your enterprise SecOps credentials
          </Typography>

          {error && (
            <ErrorAlert
              title="Authentication Failed"
              message={error}
              onRetry={() => handleLogin({ preventDefault: () => {} } as React.FormEvent)}
              onClose={() => setError(null)}
            />
          )}

          <Box component="form" onSubmit={handleLogin}>
            <Stack spacing={2.5}>
              <Box>
                <Typography variant="caption" sx={{ color: '#CBD5E1', fontWeight: 600, textTransform: 'uppercase', mb: 1, display: 'block' }}>
                  Username / ID
                </Typography>
                <TextField
                  fullWidth
                  placeholder="e.g. operator.secops"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  disabled={loading}
                  InputProps={{
                    startAdornment: (
                      <InputAdornment position="start">
                        <PersonOutlineOutlinedIcon sx={{ color: '#64748B', fontSize: 20 }} />
                      </InputAdornment>
                    ),
                    sx: {
                      bgcolor: '#1F2937',
                      color: '#F8FAFC',
                      '& fieldset': { borderColor: '#374151' },
                    },
                  }}
                />
              </Box>

              <Box>
                <Typography variant="caption" sx={{ color: '#CBD5E1', fontWeight: 600, textTransform: 'uppercase', mb: 1, display: 'block' }}>
                  Password
                </Typography>
                <TextField
                  fullWidth
                  type={showPassword ? 'text' : 'password'}
                  placeholder="••••••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  disabled={loading}
                  InputProps={{
                    startAdornment: (
                      <InputAdornment position="start">
                        <LockOutlinedIcon sx={{ color: '#64748B', fontSize: 20 }} />
                      </InputAdornment>
                    ),
                    endAdornment: (
                      <InputAdornment position="end">
                        <IconButton
                          size="small"
                          onClick={() => setShowPassword(!showPassword)}
                          edge="end"
                          sx={{ color: '#94A3B8' }}
                        >
                          {showPassword ? <VisibilityOff fontSize="small" /> : <Visibility fontSize="small" />}
                        </IconButton>
                      </InputAdornment>
                    ),
                    sx: {
                      bgcolor: '#1F2937',
                      color: '#F8FAFC',
                      fontFamily: 'monospace',
                      '& fieldset': { borderColor: '#374151' },
                    },
                  }}
                />
              </Box>

              <Button
                type="submit"
                variant="contained"
                size="large"
                fullWidth
                disabled={loading}
                endIcon={loading ? <CircularProgress size={18} color="inherit" /> : <ArrowForwardIcon />}
                sx={{
                  mt: 1,
                  py: 1.5,
                  background: 'linear-gradient(135deg, #6366F1 0%, #4F46E5 100%)',
                  boxShadow: '0 4px 18px rgba(79, 70, 229, 0.35)',
                  fontWeight: 700,
                  fontSize: '0.9375rem',
                  '&:hover': {
                    background: 'linear-gradient(135deg, #7175f7 0%, #4338CA 100%)',
                  },
                }}
              >
                {loading ? 'Authenticating...' : 'Sign In'}
              </Button>
            </Stack>
          </Box>

          <Box
            sx={{
              mt: 4,
              pt: 2.5,
              borderTop: '1px solid rgba(255, 255, 255, 0.08)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              fontSize: '0.75rem',
              color: '#94A3B8',
            }}
          >
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, color: '#34D399' }}>
              <ShieldOutlinedIcon sx={{ fontSize: 16 }} />
              <span>Zero Trust Enforced</span>
            </Box>
            <span style={{ fontFamily: 'monospace' }}>v4.12-sec</span>
          </Box>
        </CardContent>
      </Card>
    </Box>
  );
};
