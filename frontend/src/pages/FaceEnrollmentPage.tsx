import React, { useState, useCallback, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Box,
  Typography,
  Button,
  Grid,
  Card,
  CircularProgress,
  Stack,
  Alert,
} from '@mui/material';
import {
  ArrowBack as ArrowBackIcon,
  PhotoCamera as PhotoCameraIcon,
  CloudUploadOutlined as CloudUploadOutlinedIcon,
  CheckCircle as CheckCircleIcon,
  Replay as ReplayIcon,
} from '@mui/icons-material';
import {
  RealTimeFaceDetector,
  FaceDetectionStatus,
} from '../components/enrollment/RealTimeFaceDetector';
import { CaptureStatusHUD, CaptureState } from '../components/enrollment/CaptureStatusHUD';
import { PoseGuidanceHUD } from '../components/enrollment/PoseGuidanceHUD';
import { SampleGallery } from '../components/enrollment/SampleGallery';
import { CameraPermissionError } from '../components/enrollment/CameraPermissionError';
import { PhotoUploadFallback } from '../components/enrollment/PhotoUploadFallback';
import { ErrorAlert } from '../components/common/ErrorAlert';
import { faceEnrollmentService } from '../services/faceEnrollmentService';
import { GUIDED_POSES, CapturedSample } from '../services/types';

export const FaceEnrollmentPage: React.FC = () => {
  const { employeeId } = useParams<{ employeeId: string }>();
  const navigate = useNavigate();

  const [currentStepIndex, setCurrentStepIndex] = useState(0);
  const [capturedSamples, setCapturedSamples] = useState<CapturedSample[]>([]);
  const [isCapturing, setIsCapturing] = useState(false);
  const [captureState, setCaptureState] = useState<CaptureState>('position_face');
  const [detectionStatus, setDetectionStatus] = useState<FaceDetectionStatus | null>(null);

  const [cameraError, setCameraError] = useState<string | null>(null);
  const [uploadFallbackMode, setUploadFallbackMode] = useState(false);
  const [saving, setSaving] = useState(false);
  const [enrollmentComplete, setEnrollmentComplete] = useState(false);
  const [apiError, setApiError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string>('');

  const getFrameDataUrlRef = useRef<(() => string | null) | null>(null);

  const currentPoseStep = GUIDED_POSES[currentStepIndex] || GUIDED_POSES[0];

  const handleCaptureFrameReady = useCallback((fn: () => string | null) => {
    getFrameDataUrlRef.current = fn;
  }, []);

  const handleStatusChange = useCallback((status: FaceDetectionStatus) => {
    setDetectionStatus(status);

    setCaptureState((prevState) => {
      if (prevState === 'capturing' || prevState === 'captured' || prevState === 'retake') {
        return prevState;
      }
      if (status.faceCount === 0) return 'position_face';
      if (status.faceCount > 1) return 'warning';
      if (!status.isAligned) return 'align_face';
      if (status.isPoseMatched) return 'ready';
      return 'align_face';
    });
  }, []);

  const handleCameraError = useCallback((err: string) => {
    setCameraError(err);
  }, []);

  // Capture current frame for active pose step
  const handleCaptureSample = () => {
    if (!getFrameDataUrlRef.current || isCapturing) return;

    const dataUrl = getFrameDataUrlRef.current();
    if (!dataUrl) {
      setApiError('Unable to capture camera frame. Please ensure camera is active.');
      return;
    }

    setIsCapturing(true);
    setCaptureState('capturing');

    setTimeout(() => {
      const newSample: CapturedSample = {
        stepId: currentPoseStep.id,
        pose: currentPoseStep.pose,
        dataUrl,
        capturedAt: new Date().toISOString(),
      };

      const updated = [
        ...capturedSamples.filter((s) => s.stepId !== currentPoseStep.id),
        newSample,
      ];
      setCapturedSamples(updated);
      setIsCapturing(false);
      setCaptureState('captured');

      // Auto advance to next uncaptured pose
      if (currentStepIndex < GUIDED_POSES.length - 1) {
        setTimeout(() => {
          setCurrentStepIndex((prev) => prev + 1);
          setCaptureState('position_face');
        }, 500);
      }
    }, 350);
  };

  const handleRetake = (stepId: number) => {
    const targetIdx = GUIDED_POSES.findIndex((p) => p.id === stepId);
    if (targetIdx !== -1) {
      setCurrentStepIndex(targetIdx);
      setCapturedSamples((prev) => prev.filter((s) => s.stepId !== stepId));
      setCaptureState('retake');
      setTimeout(() => setCaptureState('position_face'), 600);
    }
  };

  const handleSaveToMilvus = async () => {
    if (!employeeId) return;
    setSaving(true);
    setApiError(null);

    try {
      // Ensure exactly 10 samples ordered strictly 1..10 according to GUIDED_POSES
      const orderedDataUrls = GUIDED_POSES.map((poseStep) => {
        const found = capturedSamples.find((s) => s.stepId === poseStep.id);
        if (!found) {
          throw new Error(`Missing capture for ${poseStep.label}`);
        }
        return found.dataUrl;
      });

      const res = await faceEnrollmentService.enrollFaceSamples(employeeId, orderedDataUrls);
      setSuccessMessage(
        res.message ||
          `Successfully enrolled ${res.embeddings_stored} face samples for employee ${employeeId}.`
      );
      setEnrollmentComplete(true);
    } catch (err: any) {
      setApiError(err.message || 'Face enrollment failed. Please check illumination and retry.');
    } finally {
      setSaving(false);
    }
  };

  const handleFallbackPhotoSelect = async (file: File) => {
    if (!employeeId) return;
    setSaving(true);
    setApiError(null);
    try {
      const res = await faceEnrollmentService.enrollSingleImage(employeeId, file);
      setSuccessMessage(res.message || 'Face enrolled successfully.');
      setEnrollmentComplete(true);
    } catch (err: any) {
      setApiError(err.message || 'Photo upload enrollment failed. Please ensure a clear face photo.');
    } finally {
      setSaving(false);
    }
  };

  const isAllCaptured = capturedSamples.length === GUIDED_POSES.length;
  const isReadyForCapture = detectionStatus?.isReadyToCapture || false;

  return (
    <Box>
      {/* Top Navigation & Mode Switch */}
      <Box
        sx={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          mb: 3,
        }}
      >
        <Button
          variant="text"
          color="secondary"
          startIcon={<ArrowBackIcon />}
          onClick={() => navigate(`/employees/${employeeId}`)}
          sx={{ fontWeight: 600 }}
        >
          Back to Profile ({employeeId})
        </Button>

        <Stack direction="row" spacing={1.5}>
          {!uploadFallbackMode ? (
            <Button
              variant="outlined"
              color="secondary"
              startIcon={<CloudUploadOutlinedIcon />}
              onClick={() => setUploadFallbackMode(true)}
            >
              Upload Photo Instead
            </Button>
          ) : (
            <Button
              variant="outlined"
              color="primary"
              startIcon={<PhotoCameraIcon />}
              onClick={() => setUploadFallbackMode(false)}
            >
              Switch to Live Detector
            </Button>
          )}
        </Stack>
      </Box>

      {apiError && (
        <Box sx={{ mb: 3 }}>
          <ErrorAlert
            title="Enrollment Verification Error"
            message={apiError}
            onClose={() => setApiError(null)}
          />
        </Box>
      )}

      {/* Main Studio Area */}
      {enrollmentComplete ? (
        <Card
          sx={{
            p: 6,
            textAlign: 'center',
            borderRadius: 4,
            bgcolor: '#FFFFFF',
            border: '1px solid #A7F3D0',
          }}
        >
          <Box
            sx={{
              width: 72,
              height: 72,
              borderRadius: '50%',
              bgcolor: '#ECFDF5',
              color: '#059669',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              mx: 'auto',
              mb: 2.5,
              boxShadow: '0 8px 24px rgba(16, 185, 129, 0.25)',
            }}
          >
            <CheckCircleIcon sx={{ fontSize: 44 }} />
          </Box>

          <Typography variant="h3" sx={{ fontWeight: 800, color: '#065F46', mb: 1 }}>
            Face Biometrics Successfully Enrolled
          </Typography>

          <Typography variant="body1" color="text.secondary" sx={{ maxWidth: 520, mx: 'auto', mb: 4 }}>
            {successMessage ||
              `All 10 multi-pose biometric vector embeddings have been validated by InsightFace and stored into the Milvus vector database for ${employeeId}.`}
          </Typography>

          <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center' }}>
            <Button
              variant="contained"
              color="primary"
              onClick={() => navigate(`/employees/${employeeId}`)}
              sx={{ px: 4, py: 1.25 }}
            >
              Return to Employee Profile
            </Button>
            <Button
              variant="outlined"
              startIcon={<ReplayIcon />}
              onClick={() => {
                setEnrollmentComplete(false);
                setCapturedSamples([]);
                setCurrentStepIndex(0);
              }}
            >
              Enroll Again
            </Button>
          </Box>
        </Card>
      ) : uploadFallbackMode ? (
        <PhotoUploadFallback
          onFileSelect={handleFallbackPhotoSelect}
          onSwitchToCamera={() => setUploadFallbackMode(false)}
        />
      ) : cameraError ? (
        <CameraPermissionError
          errorMessage={cameraError}
          onRetry={() => setCameraError(null)}
          onSwitchToUpload={() => setUploadFallbackMode(true)}
        />
      ) : (
        <Grid container spacing={3}>
          {/* Live Video Detector & HUD Viewport */}
          <Grid item xs={12} lg={8}>
            <Card
              sx={{
                position: 'relative',
                borderRadius: 4,
                overflow: 'hidden',
                bgcolor: '#0B0F19',
                border: '1px solid rgba(56, 189, 248, 0.35)',
                boxShadow: '0 12px 36px rgba(0, 0, 0, 0.5)',
                aspectRatio: '16/9',
                minHeight: { xs: 340, sm: 480 },
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              {/* Real-Time MediaPipe Face Detector */}
              <RealTimeFaceDetector
                targetPose={currentPoseStep.pose}
                targetPoseLabel={currentPoseStep.label}
                isCapturing={isCapturing}
                onStatusChange={handleStatusChange}
                onCameraError={handleCameraError}
                onCaptureFrameReady={handleCaptureFrameReady}
              />

              {/* Status HUD Overlaid on Camera */}
              <CaptureStatusHUD
                currentPoseLabel={currentPoseStep.label}
                instruction={currentPoseStep.instruction}
                captureState={captureState}
                liveStatusMessage={detectionStatus?.statusMessage}
                liveYawAngle={detectionStatus?.liveYawAngle}
                livePitchAngle={detectionStatus?.livePitchAngle}
              />

              {/* Bottom Capture Button */}
              <Box
                sx={{
                  position: 'absolute',
                  bottom: 20,
                  left: 0,
                  right: 0,
                  display: 'flex',
                  justifyContent: 'center',
                  zIndex: 10,
                }}
              >
                <Button
                  variant="contained"
                  size="large"
                  startIcon={
                    isCapturing ? (
                      <CircularProgress size={20} color="inherit" />
                    ) : (
                      <PhotoCameraIcon />
                    )
                  }
                  onClick={handleCaptureSample}
                  disabled={isCapturing || !isReadyForCapture}
                  sx={{
                    px: 4,
                    py: 1.25,
                    bgcolor: isReadyForCapture ? '#10B981' : '#475569',
                    boxShadow: isReadyForCapture
                      ? '0 4px 20px rgba(16, 185, 129, 0.45)'
                      : 'none',
                    fontWeight: 700,
                    borderRadius: 9999,
                    fontSize: '0.95rem',
                    transition: 'all 0.25s ease',
                    '&:hover': {
                      bgcolor: isReadyForCapture ? '#059669' : '#475569',
                    },
                  }}
                >
                  {isCapturing
                    ? 'Capturing Sample...'
                    : isReadyForCapture
                    ? `Capture Sample (${capturedSamples.length + 1}/10)`
                    : `Align Face: ${currentPoseStep.label}`}
                </Button>
              </Box>
            </Card>

            {/* Thumbnail Gallery of Captured Poses */}
            <SampleGallery
              samples={capturedSamples}
              onRetake={handleRetake}
              onClearAll={() => {
                setCapturedSamples([]);
                setCurrentStepIndex(0);
                setCaptureState('position_face');
              }}
            />
          </Grid>

          {/* Right Pose Progression Sidebar */}
          <Grid item xs={12} lg={4}>
            <PoseGuidanceHUD
              currentStepIndex={currentStepIndex}
              capturedSamples={capturedSamples}
            />

            {/* Milvus Vector Storage Submission Card */}
            <Card sx={{ mt: 3, p: 2.5, borderRadius: 3, textAlign: 'center' }}>
              <Typography variant="subtitle2" sx={{ fontWeight: 700, mb: 1 }}>
                Biometric Vector Persistence
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2.5 }}>
                {isAllCaptured
                  ? 'All 10 samples captured. Ready to submit multi-pose images to backend InsightFace extractor.'
                  : `Capture all 10 pose samples to enable submission (${capturedSamples.length}/10 complete).`}
              </Typography>

              <Button
                variant="contained"
                color="primary"
                fullWidth
                size="large"
                disabled={!isAllCaptured || saving}
                onClick={handleSaveToMilvus}
                sx={{
                  py: 1.5,
                  bgcolor: '#10B981',
                  fontWeight: 700,
                  '&:hover': { bgcolor: '#059669' },
                }}
              >
                {saving ? (
                  <CircularProgress size={22} color="inherit" />
                ) : (
                  'Submit 10 Face Samples'
                )}
              </Button>
            </Card>
          </Grid>
        </Grid>
      )}
    </Box>
  );
};
