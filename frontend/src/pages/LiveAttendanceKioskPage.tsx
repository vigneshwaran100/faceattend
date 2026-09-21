import React, { useEffect, useRef, useState, useCallback } from 'react';
import {
  Box,
  Typography,
  Chip,
  IconButton,
  Tooltip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  CircularProgress,
  Avatar,
  Snackbar,
  Alert,
  Card,
  CardContent,
  Divider,
} from '@mui/material';
import {
  CameraswitchOutlined as CameraswitchIcon,
  FiberManualRecord as FiberManualRecordIcon,
  PersonSearchOutlined as PersonSearchIcon,
  LoginOutlined as LoginIcon,
  LogoutOutlined as LogoutIcon,
  CheckCircleOutline as CheckCircleIcon,
  CancelOutlined as CancelIcon,
  ErrorOutlineOutlined as ErrorIcon,
  VisibilityOffOutlined as VisibilityOffIcon,
  VideocamOutlined as VideocamIcon,
  RadioButtonChecked as RecordIcon,
} from '@mui/icons-material';
import { FilesetResolver, FaceLandmarker } from '@mediapipe/tasks-vision';
import { kioskService } from '../services/kioskService';
import { auditLogService } from '../services/auditLogService';
import { FaceVerificationResponse, KioskStatsResponse, AuditLogRecordResponse } from '../types/api';

type ScannerMode = 'CHECK_IN' | 'CHECK_OUT';
type KioskState = 'INIT' | 'PERMISSION_DENIED' | 'DETECTING' | 'FACE_DETECTED' | 'PROCESSING' | 'SUCCESS' | 'FAILURE';

interface EventFeedItem {
  id: string;
  employee_id: string | null;
  employee_name: string | null;
  scanner_type: string;
  status: string;
  similarity: number | null;
  timestamp: string;
}

function formatTime(isoStr: string) {
  try { return new Date(isoStr).toLocaleTimeString('en-IN', { hour12: false }); } catch { return isoStr; }
}
function confidenceColor(sim: number | null): string {
  if (sim === null) return '#64748B';
  if (sim >= 0.85) return '#10B981';
  if (sim >= 0.70) return '#F59E0B';
  return '#EF4444';
}
function getInitials(name: string | null) {
  if (!name) return '?';
  return name.split(' ').map(p => p[0]).join('').toUpperCase().slice(0, 2);
}

interface LiveKioskCameraProps {
  onFaceDetected: (detected: boolean) => void;
  onGetFrame: (fn: () => Blob | null) => void;
  onCameraError: (err: string) => void;
  facePresent: boolean;
  kioskState: KioskState;
}

const LiveKioskCamera: React.FC<LiveKioskCameraProps> = ({ onFaceDetected, onGetFrame, onCameraError, facePresent }) => {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const captureCanvasRef = useRef<HTMLCanvasElement | null>(null);
  const animRef = useRef<number | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const landmarkerRef = useRef<FaceLandmarker | null>(null);
  const [fps, setFps] = useState(0);
  const lastFpsTimeRef = useRef<number>(Date.now());
  const fpsFrameCount = useRef<number>(0);

  const getFrame = useCallback((): Blob | null => {
    const video = videoRef.current;
    if (!video || video.readyState < 2) return null;
    let cap = captureCanvasRef.current;
    if (!cap) { cap = document.createElement('canvas'); captureCanvasRef.current = cap; }
    cap.width = video.videoWidth || 640;
    cap.height = video.videoHeight || 480;
    const ctx = cap.getContext('2d');
    if (!ctx) return null;
    ctx.drawImage(video, 0, 0, cap.width, cap.height);
    const dataUrl = cap.toDataURL('image/jpeg', 0.92);
    const arr = dataUrl.split(',');
    const bstr = atob(arr[1]);
    let n = bstr.length;
    const u8 = new Uint8Array(n);
    while (n--) u8[n] = bstr.charCodeAt(n);
    return new Blob([u8], { type: 'image/jpeg' });
  }, []);

  useEffect(() => { onGetFrame(getFrame); }, [getFrame, onGetFrame]);

  useEffect(() => {
    let mounted = true;
    const init = async () => {
      try {
        const filesetResolver = await FilesetResolver.forVisionTasks('https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@latest/wasm');
        const lm = await FaceLandmarker.createFromOptions(filesetResolver, {
          baseOptions: { modelAssetPath: 'https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task', delegate: 'GPU' },
          outputFaceBlendshapes: false, runningMode: 'VIDEO', numFaces: 1,
        });
        if (!mounted) { lm.close(); return; }
        landmarkerRef.current = lm;
        const stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'user', width: { ideal: 1280 }, height: { ideal: 720 } }, audio: false });
        if (!mounted) { stream.getTracks().forEach(t => t.stop()); return; }
        streamRef.current = stream;
        const video = videoRef.current!;
        video.srcObject = stream;
        await new Promise<void>(res => { video.onloadedmetadata = () => res(); });
        await video.play();

        const loop = () => {
          if (!mounted) return;
          animRef.current = requestAnimationFrame(loop);
          fpsFrameCount.current++;
          const elapsed = Date.now() - lastFpsTimeRef.current;
          if (elapsed >= 1000) { setFps(Math.round((fpsFrameCount.current * 1000) / elapsed)); fpsFrameCount.current = 0; lastFpsTimeRef.current = Date.now(); }
          if (!landmarkerRef.current || video.readyState < 2) return;
          const canvas = canvasRef.current;
          if (!canvas) return;
          canvas.width = video.videoWidth; canvas.height = video.videoHeight;
          const ctx = canvas.getContext('2d');
          if (!ctx) return;
          ctx.save(); ctx.translate(canvas.width, 0); ctx.scale(-1, 1); ctx.drawImage(video, 0, 0, canvas.width, canvas.height); ctx.restore();
          const results = landmarkerRef.current.detectForVideo(video, performance.now());
          const hasFace = results.faceLandmarks && results.faceLandmarks.length > 0;
          onFaceDetected(hasFace);
          if (hasFace) {
            const lms = results.faceLandmarks[0];
            const W = canvas.width, H = canvas.height;
            ctx.save(); ctx.fillStyle = 'rgba(99,102,241,0.7)';
            for (const l of lms) { const x = (1 - l.x) * W, y = l.y * H; ctx.beginPath(); ctx.arc(x, y, 1.5, 0, Math.PI * 2); ctx.fill(); }
            ctx.restore();
            const xs = lms.map(l => (1 - l.x) * W); const ys = lms.map(l => l.y * H);
            const minX = Math.min(...xs) - 18, maxX = Math.max(...xs) + 18, minY = Math.min(...ys) - 28, maxY = Math.max(...ys) + 18;
            const r = 10, cl = 22;
            ctx.save(); ctx.strokeStyle = '#4338CA'; ctx.lineWidth = 2; ctx.shadowColor = '#818CF8'; ctx.shadowBlur = 14;
            ctx.beginPath(); ctx.moveTo(minX + r, minY); ctx.lineTo(maxX - r, minY); ctx.arcTo(maxX, minY, maxX, minY + r, r); ctx.lineTo(maxX, maxY - r); ctx.arcTo(maxX, maxY, maxX - r, maxY, r); ctx.lineTo(minX + r, maxY); ctx.arcTo(minX, maxY, minX, maxY - r, r); ctx.lineTo(minX, minY + r); ctx.arcTo(minX, minY, minX + r, minY, r); ctx.closePath(); ctx.stroke();
            ctx.lineWidth = 3; ctx.shadowBlur = 20;
            ctx.beginPath(); ctx.moveTo(minX, minY + cl); ctx.lineTo(minX, minY); ctx.lineTo(minX + cl, minY); ctx.stroke();
            ctx.beginPath(); ctx.moveTo(maxX - cl, minY); ctx.lineTo(maxX, minY); ctx.lineTo(maxX, minY + cl); ctx.stroke();
            ctx.beginPath(); ctx.moveTo(minX, maxY - cl); ctx.lineTo(minX, maxY); ctx.lineTo(minX + cl, maxY); ctx.stroke();
            ctx.beginPath(); ctx.moveTo(maxX - cl, maxY); ctx.lineTo(maxX, maxY); ctx.lineTo(maxX, maxY - cl); ctx.stroke();
            ctx.restore();
          }
          const cx = canvas.width / 2, cy = canvas.height / 2, gl = 20;
          ctx.save(); ctx.strokeStyle = 'rgba(148,163,184,0.35)'; ctx.lineWidth = 1;
          ctx.beginPath(); ctx.moveTo(cx - 40, cy); ctx.lineTo(cx + 40, cy); ctx.stroke();
          ctx.beginPath(); ctx.moveTo(cx, cy - 40); ctx.lineTo(cx, cy + 40); ctx.stroke();
          ctx.strokeStyle = 'rgba(99,102,241,0.55)'; ctx.lineWidth = 2;
          const gx1 = cx - 70, gy1 = cy - 95, gx2 = cx + 70, gy2 = cy + 95;
          ctx.beginPath(); ctx.moveTo(gx1, gy1 + gl); ctx.lineTo(gx1, gy1); ctx.lineTo(gx1 + gl, gy1); ctx.stroke();
          ctx.beginPath(); ctx.moveTo(gx2 - gl, gy1); ctx.lineTo(gx2, gy1); ctx.lineTo(gx2, gy1 + gl); ctx.stroke();
          ctx.beginPath(); ctx.moveTo(gx1, gy2 - gl); ctx.lineTo(gx1, gy2); ctx.lineTo(gx1 + gl, gy2); ctx.stroke();
          ctx.beginPath(); ctx.moveTo(gx2 - gl, gy2); ctx.lineTo(gx2, gy2); ctx.lineTo(gx2, gy2 - gl); ctx.stroke();
          ctx.restore();
        };
        animRef.current = requestAnimationFrame(loop);
      } catch (err: any) {
        if (!mounted) return;
        if (err?.name === 'NotAllowedError' || err?.name === 'PermissionDeniedError') onCameraError('PERMISSION_DENIED');
        else onCameraError(err?.message || 'Camera error');
      }
    };
    init();
    return () => { mounted = false; if (animRef.current) cancelAnimationFrame(animRef.current); streamRef.current?.getTracks().forEach(t => t.stop()); landmarkerRef.current?.close(); };
  }, [onFaceDetected, onCameraError]);

  return (
    <Box sx={{ position: 'relative', width: '100%', height: '100%', overflow: 'hidden', borderRadius: 2.5, bgcolor: '#0F172A' }}>
      <video ref={videoRef} style={{ display: 'none' }} muted playsInline />
      <canvas ref={canvasRef} style={{ width: '100%', height: '100%', objectFit: 'cover', display: 'block' }} />
      <Box sx={{ position: 'absolute', top: 10, right: 12, fontFamily: 'monospace', fontSize: '0.6rem', color: '#94A3B8', bgcolor: 'rgba(15,23,42,0.7)', px: 1, py: 0.3, borderRadius: 1, letterSpacing: 1 }}>{fps} FPS</Box>
      <Box sx={{
        position: 'absolute', bottom: 14, left: '50%', transform: 'translateX(-50%)',
        display: 'flex', alignItems: 'center', gap: 1, px: 2, py: 0.7,
        bgcolor: facePresent ? 'rgba(67,56,202,0.85)' : 'rgba(15,23,42,0.75)',
        borderRadius: 10, border: '1px solid', borderColor: facePresent ? '#818CF8' : '#334155',
        backdropFilter: 'blur(8px)', whiteSpace: 'nowrap',
        transition: 'all 0.25s',
      }}>
        <FiberManualRecordIcon sx={{ fontSize: 9, color: facePresent ? '#A5B4FC' : '#475569' }} />
        <Typography sx={{ fontFamily: 'monospace', fontSize: '0.65rem', color: facePresent ? '#E0E7FF' : '#64748B', letterSpacing: 1.2, fontWeight: 600 }}>
          {facePresent ? 'FACE DETECTED · SCANNING' : 'STEP INTO FRAME'}
        </Typography>
      </Box>
    </Box>
  );
};

export const LiveAttendanceKioskPage: React.FC = () => {
  const [mode, setMode] = useState<ScannerMode>('CHECK_IN');
  const [kioskState, setKioskState] = useState<KioskState>('INIT');
  const [facePresent, setFacePresent] = useState(false);
  const [lastResult, setLastResult] = useState<FaceVerificationResponse | null>(null);
  const [stats, setStats] = useState<KioskStatsResponse | null>(null);
  const [eventFeed, setEventFeed] = useState<EventFeedItem[]>([]);
  const [manualDialogOpen, setManualDialogOpen] = useState(false);
  const [manualEmpId, setManualEmpId] = useState('');
  const [manualMode, setManualMode] = useState<ScannerMode>('CHECK_IN');
  const [manualLoading, setManualLoading] = useState(false);
  const [snack, setSnack] = useState<{ msg: string; severity: 'success' | 'error' } | null>(null);
  const [clock, setClock] = useState('');
  const getFrameRef = useRef<(() => Blob | null) | null>(null);
  const processingRef = useRef(false);
  const bannerTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    const update = () => setClock(new Date().toLocaleTimeString('en-IN', { hour12: false }));
    update();
    const id = setInterval(update, 1000);
    return () => clearInterval(id);
  }, []);

  const handleCameraError = useCallback((err: string) => { setKioskState(err === 'PERMISSION_DENIED' ? 'PERMISSION_DENIED' : 'FAILURE'); }, []);
  const handleGetFrame = useCallback((fn: () => Blob | null) => { getFrameRef.current = fn; setKioskState('DETECTING'); }, []);
  const handleFaceDetected = useCallback((detected: boolean) => { setFacePresent(detected); setKioskState(st => (st === 'DETECTING' || st === 'FACE_DETECTED') ? (detected ? 'FACE_DETECTED' : 'DETECTING') : st); }, []);

  const lastCaptureRef = useRef<number>(0);
  useEffect(() => {
    if (!facePresent || processingRef.current || kioskState !== 'FACE_DETECTED') return;
    if (Date.now() - lastCaptureRef.current < 4000) return;
    const timer = setTimeout(async () => {
      if (!getFrameRef.current || processingRef.current) return;
      const blob = getFrameRef.current();
      if (!blob) return;
      processingRef.current = true;
      setKioskState('PROCESSING');
      lastCaptureRef.current = Date.now();
      const reset = (delay = 3000) => { if (bannerTimeoutRef.current) clearTimeout(bannerTimeoutRef.current); bannerTimeoutRef.current = setTimeout(() => { setKioskState('DETECTING'); setLastResult(null); processingRef.current = false; }, delay); };
      try {
        const result = await kioskService.verifyFaceAndPunch(blob, mode);
        setLastResult(result);
        setKioskState(result.success ? 'SUCCESS' : 'FAILURE');
        if (result.success) addToFeed(result);
        reset();
      } catch (err: any) {
        setLastResult({ success: false, status: 'ERROR', message: err?.message || 'Network error', employee_id: null, employee_name: null, department: null, job_title: null, similarity: null, scanner_type: mode, timestamp: new Date().toISOString(), attendance_id: null });
        setKioskState('FAILURE');
        reset();
      }
    }, 1200);
    return () => clearTimeout(timer);
  }, [facePresent, kioskState, mode]);

  function addToFeed(result: FaceVerificationResponse) {
    setEventFeed(prev => [{ id: result.timestamp + (result.employee_id ?? ''), employee_id: result.employee_id, employee_name: result.employee_name, scanner_type: result.scanner_type, status: result.status, similarity: result.similarity, timestamp: result.timestamp }, ...prev.slice(0, 49)]);
  }

  useEffect(() => {
    const fetchStats = async () => { try { setStats(await kioskService.getKioskStats()); } catch { } };
    fetchStats(); const id = setInterval(fetchStats, 30000); return () => clearInterval(id);
  }, []);

  useEffect(() => {
    const fetchLogs = async () => { try { const today = new Date().toISOString().split('T')[0]; const logs = await auditLogService.getLogs({ start_date: today, end_date: today, page: 1, page_size: 20 }); setEventFeed(logs.items.map((l: AuditLogRecordResponse) => ({ id: String(l.log_id), employee_id: l.employee_id, employee_name: l.employee_id, scanner_type: l.scanner_type, status: l.status === 'SUCCESS' ? 'ACCESS_GRANTED' : 'REJECTED', similarity: l.similarity, timestamp: l.created_at }))); } catch { } };
    fetchLogs();
  }, []);

  const handleManualPunch = async () => {
    if (!manualEmpId.trim()) return;
    setManualLoading(true);
    try {
      const r = await kioskService.manualPunch({ employee_id: manualEmpId.trim(), scanner_type: manualMode });
      addToFeed(r);
      setSnack({ msg: 'Manual ' + manualMode + ' for ' + (r.employee_name ?? manualEmpId), severity: 'success' });
      setManualDialogOpen(false);
      setManualEmpId('');
    } catch (e: any) {
      setSnack({ msg: e?.message || 'Manual punch failed', severity: 'error' });
    } finally {
      setManualLoading(false);
    }
  };

  const getBanner = () => {
    if (!lastResult) return null;
    if (kioskState === 'SUCCESS') return {
      color: '#059669', bg: '#ECFDF5', border: '#A7F3D0',
      icon: <CheckCircleIcon sx={{ fontSize: 28 }} />,
      title: mode === 'CHECK_IN' ? 'Check-In Recorded' : 'Check-Out Recorded',
      sub: lastResult.employee_name ?? '', sim: lastResult.similarity
    };
    if (kioskState === 'FAILURE') {
      const icons: Record<string, React.ReactNode> = {
        UNRECOGNIZED_FACE: <PersonSearchIcon sx={{ fontSize: 28 }} />,
        NO_FACE_DETECTED: <VisibilityOffIcon sx={{ fontSize: 28 }} />,
        MULTIPLE_FACES_DETECTED: <CancelIcon sx={{ fontSize: 28 }} />,
        QUALITY_FAILED: <VisibilityOffIcon sx={{ fontSize: 28 }} />,
        EMPLOYEE_NOT_FOUND: <PersonSearchIcon sx={{ fontSize: 28 }} />,
        INACTIVE_EMPLOYEE: <CancelIcon sx={{ fontSize: 28 }} />,
        NO_CHECK_IN: <CancelIcon sx={{ fontSize: 28 }} />,
        ERROR: <ErrorIcon sx={{ fontSize: 28 }} />
      };
      return {
        color: '#DC2626', bg: '#FEF2F2', border: '#FECACA',
        icon: icons[lastResult.status] ?? <CancelIcon sx={{ fontSize: 28 }} />,
        title: lastResult.status.replace(/_/g, ' '),
        sub: lastResult.message, sim: lastResult.similarity
      };
    }
    return null;
  };

  const banner = getBanner();
  const dateStr = new Date().toLocaleDateString('en-IN', { weekday: 'short', year: 'numeric', month: 'short', day: 'numeric' });

  const stateLabel: Record<KioskState, string> = {
    INIT: 'Initializing',
    PERMISSION_DENIED: 'Camera Denied',
    DETECTING: 'Scanning',
    FACE_DETECTED: 'Face Detected',
    PROCESSING: 'Verifying',
    SUCCESS: 'Access Granted',
    FAILURE: 'Access Denied',
  };
  const stateColor: Record<KioskState, string> = {
    INIT: '#F59E0B',
    PERMISSION_DENIED: '#EF4444',
    DETECTING: '#64748B',
    FACE_DETECTED: '#4338CA',
    PROCESSING: '#6366F1',
    SUCCESS: '#10B981',
    FAILURE: '#EF4444',
  };

  return (
    <Box sx={{
      display: 'flex',
      flexDirection: 'column',
      m: { xs: -2.5, md: -4 },
      height: 'calc(100% + 64px)',
      minHeight: 0,
      bgcolor: '#F8FAFC',
      overflow: 'hidden',
    }}>
      {/* Page Header */}
      <Box sx={{
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        px: 3, py: 1.5,
        bgcolor: '#FFFFFF',
        borderBottom: '1px solid #E2E8F0',
        flexShrink: 0,
      }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <Box sx={{ width: 36, height: 36, borderRadius: 2, bgcolor: '#EEF2FF', color: '#4338CA', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <RecordIcon sx={{ fontSize: 20 }} />
          </Box>
          <Box>
            <Typography variant="h6" sx={{ fontWeight: 800, color: '#0F172A', lineHeight: 1.1 }}>Live Attendance Kiosk</Typography>
            <Typography variant="caption" color="text.secondary">Gate-01A · Real-time biometric check-in / check-out</Typography>
          </Box>
          <Chip
            size="small"
            label={stateLabel[kioskState]}
            sx={{
              ml: 1,
              bgcolor: stateColor[kioskState] + '18',
              color: stateColor[kioskState],
              border: '1px solid ' + stateColor[kioskState] + '44',
              fontWeight: 600,
              fontSize: '0.7rem',
            }}
          />
        </Box>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <Typography sx={{ fontFamily: 'monospace', color: '#4338CA', fontWeight: 700, fontSize: '0.85rem' }}>{clock}</Typography>
          <Typography variant="caption" color="text.secondary">{dateStr}</Typography>
        </Box>
      </Box>

      {/* Main Body */}
      <Box sx={{ display: 'flex', flex: 1, overflow: 'hidden', minHeight: 0 }}>

        {/* Camera Panel */}
        <Box sx={{ flex: 1, display: 'flex', flexDirection: 'column', minWidth: 0, p: 2, gap: 2 }}>
          {banner && (kioskState === 'SUCCESS' || kioskState === 'FAILURE') && (
            <Box sx={{
              display: 'flex', alignItems: 'center', gap: 2, px: 3, py: 1.5,
              bgcolor: banner.bg, border: '1px solid ' + banner.border, borderRadius: 2, flexShrink: 0,
            }}>
              <Box sx={{ color: banner.color, display: 'flex' }}>{banner.icon}</Box>
              <Box sx={{ flex: 1 }}>
                <Typography sx={{ fontWeight: 700, color: banner.color, fontSize: '0.95rem' }}>{banner.title}</Typography>
                {banner.sub && <Typography variant="caption" color="text.secondary">{banner.sub}</Typography>}
              </Box>
              {banner.sim != null && (
                <Chip size="small"
                  label={(banner.sim * 100).toFixed(1) + '% confidence'}
                  sx={{ bgcolor: confidenceColor(banner.sim) + '18', color: confidenceColor(banner.sim), border: '1px solid ' + confidenceColor(banner.sim) + '44', fontWeight: 600, fontSize: '0.7rem', fontFamily: 'monospace' }}
                />
              )}
            </Box>
          )}

          <Box sx={{ flex: 1, position: 'relative', borderRadius: 2.5, overflow: 'hidden', border: '1px solid #E2E8F0', bgcolor: '#0F172A', minHeight: 0, boxShadow: '0 4px 24px rgba(15,23,42,0.12)' }}>
            {kioskState === 'PERMISSION_DENIED' ? (
              <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%', bgcolor: '#0F172A', gap: 2 }}>
                <VideocamIcon sx={{ fontSize: 64, color: '#334155' }} />
                <Typography sx={{ color: '#94A3B8', fontWeight: 600, fontSize: '0.9rem' }}>Camera Permission Denied</Typography>
                <Typography sx={{ color: '#64748B', fontSize: '0.75rem', textAlign: 'center', maxWidth: 300 }}>Allow camera access in browser settings and refresh the page.</Typography>
              </Box>
            ) : (
              <LiveKioskCamera
                onFaceDetected={handleFaceDetected}
                onGetFrame={handleGetFrame}
                onCameraError={handleCameraError}
                facePresent={facePresent}
                kioskState={kioskState}
              />
            )}
            {kioskState === 'INIT' && (
              <Box sx={{ position: 'absolute', inset: 0, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', bgcolor: 'rgba(15,23,42,0.9)', gap: 2 }}>
                <CircularProgress size={40} sx={{ color: '#818CF8' }} />
                <Typography sx={{ color: '#E0E7FF', fontFamily: 'monospace', fontSize: '0.8rem', letterSpacing: 1 }}>INITIALIZING FACE ENGINE</Typography>
              </Box>
            )}
            {kioskState === 'PROCESSING' && (
              <Box sx={{ position: 'absolute', inset: 0, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', bgcolor: 'rgba(15,23,42,0.75)', gap: 2, backdropFilter: 'blur(4px)' }}>
                <CircularProgress size={36} sx={{ color: '#818CF8' }} />
                <Typography sx={{ color: '#E0E7FF', fontFamily: 'monospace', fontSize: '0.78rem', letterSpacing: 1.5 }}>VERIFYING IDENTITY</Typography>
              </Box>
            )}
            <Box sx={{ position: 'absolute', top: 10, left: 12 }}>
              <Tooltip title="Switch Camera" placement="right">
                <IconButton size="small" sx={{ bgcolor: 'rgba(15,23,42,0.7)', color: '#94A3B8', '&:hover': { color: '#E0E7FF', bgcolor: 'rgba(67,56,202,0.6)' } }}>
                  <CameraswitchIcon fontSize="small" />
                </IconButton>
              </Tooltip>
            </Box>
          </Box>
        </Box>

        {/* Right Sidebar */}
        <Box sx={{ width: 296, display: 'flex', flexDirection: 'column', borderLeft: '1px solid #E2E8F0', bgcolor: '#FFFFFF', flexShrink: 0, overflow: 'hidden' }}>

          {/* Mode Toggle */}
          <Box sx={{ p: 2, borderBottom: '1px solid #E2E8F0' }}>
            <Typography variant="overline" sx={{ color: '#94A3B8', letterSpacing: 2, fontSize: '0.62rem' }}>Scanner Mode</Typography>
            <Box sx={{ display: 'flex', borderRadius: 1.5, overflow: 'hidden', border: '1px solid #E2E8F0', mt: 1 }}>
              {(['CHECK_IN', 'CHECK_OUT'] as ScannerMode[]).map(m => (
                <Box
                  key={m}
                  onClick={() => setMode(m)}
                  sx={{
                    flex: 1, py: 1.1, textAlign: 'center', cursor: 'pointer',
                    bgcolor: mode === m ? (m === 'CHECK_IN' ? '#EEF2FF' : '#FAF5FF') : 'transparent',
                    borderRight: m === 'CHECK_IN' ? '1px solid #E2E8F0' : 'none',
                    transition: 'all 0.15s',
                    '&:hover': { bgcolor: m === 'CHECK_IN' ? '#EEF2FF' : '#FAF5FF' },
                  }}
                >
                  {m === 'CHECK_IN'
                    ? <LoginIcon sx={{ fontSize: 14, color: mode === m ? '#4338CA' : '#94A3B8', mr: 0.5, verticalAlign: 'middle' }} />
                    : <LogoutIcon sx={{ fontSize: 14, color: mode === m ? '#7C3AED' : '#94A3B8', mr: 0.5, verticalAlign: 'middle' }} />
                  }
                  <Typography component="span" sx={{ fontSize: '0.7rem', fontWeight: 700, color: mode === m ? (m === 'CHECK_IN' ? '#4338CA' : '#7C3AED') : '#94A3B8' }}>
                    {m === 'CHECK_IN' ? 'Check-In' : 'Check-Out'}
                  </Typography>
                </Box>
              ))}
            </Box>
          </Box>

          {/* Stats Grid */}
          <Box sx={{ p: 2, borderBottom: '1px solid #E2E8F0' }}>
            <Typography variant="overline" sx={{ color: '#94A3B8', letterSpacing: 2, fontSize: '0.62rem' }}>Today's Statistics</Typography>
            <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 1, mt: 1 }}>
              {[
                { label: 'Total Scans', value: stats?.total_scans_today ?? '', color: '#4338CA' },
                { label: 'Verified', value: stats?.successful_punches ?? '', color: '#059669' },
                { label: 'Rejected', value: stats?.rejected_scans ?? '', color: '#DC2626' },
                { label: 'Checked In', value: stats?.checked_in_count ?? '', color: '#0369A1' },
              ].map(s => (
                <Card key={s.label} variant="outlined" sx={{ borderColor: '#E2E8F0', borderRadius: 2 }}>
                  <CardContent sx={{ p: '10px !important', textAlign: 'center' }}>
                    <Typography sx={{ fontFamily: 'monospace', fontSize: '1.2rem', fontWeight: 800, color: s.color }}>{s.value}</Typography>
                    <Typography sx={{ fontSize: '0.6rem', color: '#94A3B8', fontWeight: 600, letterSpacing: 0.5, mt: 0.2, textTransform: 'uppercase' }}>{s.label}</Typography>
                  </CardContent>
                </Card>
              ))}
            </Box>
          </Box>

          {/* Event Feed */}
          <Box sx={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
            <Box sx={{ px: 2, py: 1.5, borderBottom: '1px solid #E2E8F0', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <Typography variant="overline" sx={{ color: '#94A3B8', letterSpacing: 2, fontSize: '0.62rem' }}>Live Event Feed</Typography>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                <Box sx={{ width: 6, height: 6, borderRadius: '50%', bgcolor: '#10B981', animation: 'pulse 1.5s infinite' }} />
                <Typography sx={{ fontSize: '0.62rem', color: '#10B981', fontWeight: 600 }}>LIVE</Typography>
              </Box>
            </Box>
            <Box sx={{ flex: 1, overflowY: 'auto', '&::-webkit-scrollbar': { width: 4 }, '&::-webkit-scrollbar-thumb': { bgcolor: '#E2E8F0', borderRadius: 2 } }}>
              {eventFeed.length === 0
                ? <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: 80 }}>
                  <Typography variant="caption" color="text.secondary">No events yet today</Typography>
                </Box>
                : eventFeed.map(ev => {
                  const isGrant = ev.status === 'ACCESS_GRANTED' || ev.status === 'SUCCESS';
                  return (
                    <Box key={ev.id} sx={{ px: 2, py: 1, borderBottom: '1px solid #F1F5F9', display: 'flex', alignItems: 'center', gap: 1.5, '&:hover': { bgcolor: '#F8FAFC' } }}>
                      <Avatar sx={{ width: 30, height: 30, fontSize: '0.62rem', fontWeight: 700, bgcolor: isGrant ? '#ECFDF5' : '#FEF2F2', color: isGrant ? '#059669' : '#DC2626', border: '1.5px solid', borderColor: isGrant ? '#A7F3D0' : '#FECACA' }}>
                        {getInitials(ev.employee_name)}
                      </Avatar>
                      <Box sx={{ flex: 1, minWidth: 0 }}>
                        <Typography sx={{ fontSize: '0.75rem', color: '#0F172A', fontWeight: 600, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{ev.employee_name ?? ev.employee_id ?? 'Unknown'}</Typography>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 0.2 }}>
                          <Typography sx={{ fontFamily: 'monospace', fontSize: '0.6rem', color: '#94A3B8' }}>{formatTime(ev.timestamp)}</Typography>
                          <Typography sx={{ fontSize: '0.6rem', color: ev.scanner_type === 'CHECK_IN' ? '#4338CA' : '#7C3AED', fontWeight: 600 }}>{ev.scanner_type?.replace('_', '-')}</Typography>
                        </Box>
                      </Box>
                      {ev.similarity != null && (
                        <Typography sx={{ fontFamily: 'monospace', fontSize: '0.65rem', color: confidenceColor(ev.similarity), fontWeight: 700, flexShrink: 0 }}>
                          {(ev.similarity * 100).toFixed(0)}%
                        </Typography>
                      )}
                    </Box>
                  );
                })
              }
            </Box>
          </Box>

          <Divider />
          <Box sx={{ p: 2 }}>
            <Button
              fullWidth variant="outlined" size="small"
              onClick={() => setManualDialogOpen(true)}
              startIcon={<PersonSearchIcon />}
              sx={{ borderColor: '#E2E8F0', color: '#475569', py: 1, fontWeight: 600, '&:hover': { borderColor: '#4338CA', color: '#4338CA', bgcolor: '#EEF2FF' } }}
            >
              Manual Override / Badge Punch
            </Button>
          </Box>
        </Box>
      </Box>

      {/* Manual Punch Dialog */}
      <Dialog open={manualDialogOpen} onClose={() => setManualDialogOpen(false)} PaperProps={{ sx: { borderRadius: 3, minWidth: 360 } }}>
        <DialogTitle sx={{ fontWeight: 700, color: '#0F172A', borderBottom: '1px solid #E2E8F0', pb: 1.5 }}>Manual Badge Punch</DialogTitle>
        <DialogContent sx={{ pt: 2.5, display: 'flex', flexDirection: 'column', gap: 2 }}>
          <Typography variant="caption" color="text.secondary">Security operator override  logged in audit trail.</Typography>
          <TextField label="Employee ID" value={manualEmpId} onChange={e => setManualEmpId(e.target.value)} size="small" fullWidth onKeyDown={e => e.key === 'Enter' && handleManualPunch()} />
          <FormControl size="small" fullWidth>
            <InputLabel>Mode</InputLabel>
            <Select value={manualMode} label="Mode" onChange={e => setManualMode(e.target.value as ScannerMode)}>
              <MenuItem value="CHECK_IN">Check-In</MenuItem>
              <MenuItem value="CHECK_OUT">Check-Out</MenuItem>
            </Select>
          </FormControl>
        </DialogContent>
        <DialogActions sx={{ borderTop: '1px solid #E2E8F0', px: 2, py: 1.5 }}>
          <Button onClick={() => setManualDialogOpen(false)} color="inherit">Cancel</Button>
          <Button onClick={handleManualPunch} disabled={!manualEmpId.trim() || manualLoading} variant="contained" sx={{ bgcolor: '#4338CA', '&:hover': { bgcolor: '#3730A3' }, '&:disabled': { bgcolor: '#E2E8F0', color: '#94A3B8' } }}>
            {manualLoading ? <CircularProgress size={14} sx={{ color: '#fff' }} /> : 'Confirm Punch'}
          </Button>
        </DialogActions>
      </Dialog>

      <Snackbar open={!!snack} autoHideDuration={4000} onClose={() => setSnack(null)} anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}>
        <Alert severity={snack?.severity ?? 'info'} onClose={() => setSnack(null)} sx={{ fontWeight: 600 }}>{snack?.msg}</Alert>
      </Snackbar>

      <style dangerouslySetInnerHTML={{ __html: '@keyframes pulse{0%,100%{opacity:1}50%{opacity:0.4}}' }} />
    </Box>
  );
};
