import React from 'react';
import { Outlet } from 'react-router-dom';
import { Box, Typography } from '@mui/material';

export const AuthLayout: React.FC = () => {
  return (
    <Box
      sx={{
        minHeight: '100vh',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'space-between',
        background: 'radial-gradient(circle at 50% 30%, #151b2e 0%, #0B0F19 75%, #080b12 100%)',
        color: '#F8FAFC',
        p: { xs: 2, sm: 4 },
      }}
    >
      {/* Top Header */}
      <Box
        component="header"
        sx={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
          pb: 2,
          fontSize: '0.75rem',
          color: '#94A3B8',
          fontFamily: 'monospace',
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Box sx={{ width: 6, height: 6, borderRadius: '50%', bgcolor: '#10B981' }} />
          <span>SOC-SECURE-PORTAL</span>
          <span style={{ color: '#475569' }}>|</span>
          <span>MILVUS VECTOR PIPELINE</span>
        </Box>

        <Box sx={{ display: 'flex', gap: 2 }}>
          <span>ENCRYPTED FIPS-140-3</span>
          <span style={{ color: '#475569' }}>•</span>
          <span>TLS 1.3</span>
        </Box>
      </Box>

      {/* Auth Viewport */}
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', my: 'auto', py: 4 }}>
        <Outlet />
      </Box>

      {/* Compliance Footer */}
      <Box
        component="footer"
        sx={{
          display: 'flex',
          flexDirection: { xs: 'column', sm: 'row' },
          alignItems: 'center',
          justifyContent: 'space-between',
          borderTop: '1px solid rgba(255, 255, 255, 0.08)',
          pt: 2,
          fontSize: '0.75rem',
          color: '#64748B',
          gap: 1,
        }}
      >
        <Typography variant="caption" sx={{ color: '#64748B' }}>
          © 2026 FaceAttend Biometric Systems Inc. Strictly for authorized enterprise personnel.
        </Typography>
        <Typography variant="caption" sx={{ color: '#64748B', fontFamily: 'monospace' }}>
          SOC2 Type II • ISO 27001 • Biometric Privacy Shield
        </Typography>
      </Box>
    </Box>
  );
};
