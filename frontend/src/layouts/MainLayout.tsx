import React, { useState, useEffect } from 'react';
import { Outlet, NavLink, useNavigate, useLocation } from 'react-router-dom';
import {
  Box,
  Typography,
  IconButton,
  Tooltip,
  Avatar,
  Divider,
} from '@mui/material';
import {
  DashboardOutlined as DashboardOutlinedIcon,
  PeopleAltOutlined as PeopleAltOutlinedIcon,
  CalendarMonthOutlined as CalendarMonthOutlinedIcon,
  FactCheckOutlined as FactCheckOutlinedIcon,
  CorporateFareOutlined as CorporateFareOutlinedIcon,
  LogoutOutlined as LogoutOutlinedIcon,
  VideocamOutlined as VideocamOutlinedIcon,
} from '@mui/icons-material';
import { ReadinessBanner } from '../components/common/ReadinessBanner';
import { useReadiness } from '../hooks/useReadiness';
import { authService } from '../services/authService';

export const MainLayout: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const [clock, setClock] = useState('');
  const { readiness: readinessStatus, refetch: refetchReadiness } = useReadiness(30000);

  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      setClock(now.toLocaleTimeString('en-US', { hour12: false }));
    };
    updateTime();
    const timer = setInterval(updateTime, 1000);
    return () => clearInterval(timer);
  }, []);

  const navItems = [
    { label: 'Dashboard', path: '/dashboard', icon: <DashboardOutlinedIcon fontSize="small" /> },
    { label: 'Employees', path: '/employees', icon: <PeopleAltOutlinedIcon fontSize="small" /> },
    { label: 'Attendance Records', path: '/attendance', icon: <CalendarMonthOutlinedIcon fontSize="small" /> },
    { label: 'Live Kiosk', path: '/kiosk', icon: <VideocamOutlinedIcon fontSize="small" />, accent: '#22D3EE' },
    { label: 'Scanner Audit Logs', path: '/audit-logs', icon: <FactCheckOutlinedIcon fontSize="small" /> },
    { label: 'Organization', path: '/organization', icon: <CorporateFareOutlinedIcon fontSize="small" /> },
  ];

  const handleLogout = () => {
    authService.logout();
    navigate('/login');
  };

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', height: '100vh', bgcolor: 'background.default' }}>
      {/* Top Global Telemetry Header */}
      <Box
        component="header"
        sx={{
          bgcolor: '#0F172A',
          color: '#94A3B8',
          px: 3,
          py: 1,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          fontSize: '0.75rem',
          borderBottom: '1px solid #1E293B',
          userSelect: 'none',
          flexShrink: 0,
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, fontFamily: 'monospace' }}>
            <Box
              sx={{
                width: 7,
                height: 7,
                borderRadius: '50%',
                bgcolor: readinessStatus.dependencies.database.status === 'healthy' ? '#10B981' : '#EF4444',
              }}
            />
            <Typography variant="caption" sx={{ fontFamily: 'monospace', color: '#CBD5E1', fontWeight: 600 }}>
              POSTGRES READY
            </Typography>
          </Box>

          <Typography variant="caption" sx={{ color: '#475569' }}>|</Typography>

          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, fontFamily: 'monospace' }}>
            <Box
              sx={{
                width: 7,
                height: 7,
                borderRadius: '50%',
                bgcolor: readinessStatus.dependencies.milvus.status === 'healthy' ? '#10B981' : '#F59E0B',
              }}
            />
            <Typography variant="caption" sx={{ fontFamily: 'monospace', color: '#CBD5E1', fontWeight: 600 }}>
              MILVUS {readinessStatus.dependencies.milvus.status === 'healthy' ? 'ONLINE' : 'DEGRADED'}
            </Typography>
          </Box>
        </Box>

        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2.5 }}>
          <Typography variant="caption" sx={{ fontFamily: 'monospace', color: '#818CF8', fontWeight: 700 }}>
            {clock || '00:00:00'}
          </Typography>

          <Divider orientation="vertical" flexItem sx={{ borderColor: '#334155' }} />

          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
            <Avatar sx={{ width: 24, height: 24, bgcolor: '#4338CA', fontSize: '0.7rem', fontWeight: 700 }}>
              A
            </Avatar>
            <Typography variant="caption" sx={{ color: '#E2E8F0', fontWeight: 600 }}>
              Admin Operator
            </Typography>
            <Tooltip title="Sign Out">
              <IconButton size="small" onClick={handleLogout} sx={{ color: '#94A3B8', '&:hover': { color: '#EF4444' } }}>
                <LogoutOutlinedIcon sx={{ fontSize: 16 }} />
              </IconButton>
            </Tooltip>
          </Box>
        </Box>
      </Box>

      {/* Main Body with Sidebar and Viewport */}
      <Box sx={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
        {/* Persistent Left Sidebar */}
        <Box
          component="aside"
          sx={{
            width: 260,
            bgcolor: '#FFFFFF',
            borderRight: '1px solid #E2E8F0',
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'space-between',
            flexShrink: 0,
            p: 2.5,
          }}
        >
          <Box>
            {/* Brand Logo */}
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 4, px: 1 }}>
              <Box
                sx={{
                  width: 36,
                  height: 36,
                  borderRadius: 2.5,
                  bgcolor: '#4338CA',
                  color: '#FFFFFF',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  boxShadow: '0 4px 12px rgba(67, 56, 202, 0.25)',
                }}
              >
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M3 7V5a2 2 0 0 1 2-2h2" />
                  <path d="M17 3h2a2 2 0 0 1 2 2v2" />
                  <path d="M21 17v2a2 2 0 0 1-2 2h-2" />
                  <path d="M7 21H5a2 2 0 0 1-2-2v-2" />
                  <circle cx="12" cy="11" r="3" />
                  <path d="M9 16c.8 1.2 2 2 3 2s2.2-.8 3-2" />
                </svg>
              </Box>
              <Box>
                <Typography variant="h6" sx={{ fontWeight: 800, lineHeight: 1.1, color: '#0F172A' }}>
                  Face<span style={{ color: '#4338CA' }}>Attend</span>
                </Typography>
                <Typography variant="overline" sx={{ fontSize: '0.625rem', color: '#94A3B8', letterSpacing: '0.08em' }}>
                  Enterprise Shell
                </Typography>
              </Box>
            </Box>

            {/* Nav Links */}
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5 }}>
              {navItems.map((item) => {
                const isActive = location.pathname.startsWith(item.path);

                return (
                  <NavLink
                    key={item.path}
                    to={item.path}
                    style={{ textDecoration: 'none' }}
                  >
                    <Box
                      sx={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: 1.5,
                        px: 2,
                        py: 1.25,
                        borderRadius: 2,
                        color: isActive ? '#4338CA' : '#475569',
                        bgcolor: isActive ? '#EEF2FF' : 'transparent',
                        fontWeight: isActive ? 700 : 500,
                        fontSize: '0.875rem',
                        transition: 'all 0.15s ease-in-out',
                        '&:hover': {
                          bgcolor: isActive ? '#EEF2FF' : '#F8FAFC',
                          color: isActive ? '#4338CA' : '#0F172A',
                        },
                      }}
                    >
                      <Box sx={{ color: isActive ? '#4338CA' : '#94A3B8', display: 'flex', alignItems: 'center' }}>
                        {item.icon}
                      </Box>
                      <span>{item.label}</span>
                    </Box>
                  </NavLink>
                );
              })}
            </Box>
          </Box>

          {/* Footer Info Box */}
          <Box sx={{ p: 2, bgcolor: '#F8FAFC', borderRadius: 2.5, border: '1px solid #E2E8F0' }}>
            <Typography variant="caption" sx={{ fontWeight: 700, color: '#0F172A', display: 'block', mb: 0.5 }}>
              Hardware Kiosk Mode
            </Typography>
            <Typography variant="caption" sx={{ color: '#64748B', display: 'block', lineHeight: 1.4 }}>
              Standalone OpenCV scanning running on edge device nodes.
            </Typography>
          </Box>
        </Box>

        {/* Dynamic Viewport Container */}
        <Box
          component="main"
          sx={{
            flex: 1,
            overflowY: 'auto',
            p: { xs: 2.5, md: 4 },
          }}
        >
          <ReadinessBanner
            status={readinessStatus}
            onRetry={refetchReadiness}
          />
          <Outlet />
        </Box>
      </Box>
    </Box>
  );
};
