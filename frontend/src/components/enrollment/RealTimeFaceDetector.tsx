import React, { useEffect, useRef, useState, useCallback } from 'react';
import { Box, Typography, CircularProgress, Chip } from '@mui/material';
import { FilesetResolver, FaceLandmarker, NormalizedLandmark } from '@mediapipe/tasks-vision';

export interface FaceDetectionStatus {
  faceCount: number;
  isAligned: boolean;
  isPoseMatched: boolean;
  currentEstimatedPose: 'FRONT' | 'LEFT' | 'RIGHT' | 'UP' | 'DOWN' | 'UNKNOWN';
  liveYawAngle: number;
  livePitchAngle: number;
  statusMessage: string;
  isReadyToCapture: boolean;
}

interface RealTimeFaceDetectorProps {
  targetPose: 'FRONT' | 'LEFT' | 'RIGHT' | 'UP' | 'DOWN';
  targetPoseLabel: string;
  isCapturing: boolean;
  onStatusChange: (status: FaceDetectionStatus) => void;
  onCameraError: (error: string) => void;
  onCaptureFrameReady: (getFrameDataUrl: () => string | null) => void;
}

export const RealTimeFaceDetector: React.FC<RealTimeFaceDetectorProps> = ({
  targetPose,
  targetPoseLabel,
  isCapturing,
  onStatusChange,
  onCameraError,
  onCaptureFrameReady,
}) => {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const captureCanvasRef = useRef<HTMLCanvasElement>(null);

  const landmarkerRef = useRef<FaceLandmarker | null>(null);
  const animFrameIdRef = useRef<number | null>(null);
  const streamRef = useRef<MediaStream | null>(null);

  const [modelLoading, setModelLoading] = useState(true);
  const [modelError, setModelError] = useState<string | null>(null);
  const [cameraStarted, setCameraStarted] = useState(false);

  // Expose frame capture function to parent
  const getFrameDataUrl = useCallback((): string | null => {
    const video = videoRef.current;
    if (!video || video.readyState < 2) return null;

    let captureCanvas = captureCanvasRef.current;
    if (!captureCanvas) {
      captureCanvas = document.createElement('canvas');
      captureCanvasRef.current = captureCanvas;
    }

    captureCanvas.width = video.videoWidth || 1280;
    captureCanvas.height = video.videoHeight || 720;

    const ctx = captureCanvas.getContext('2d');
    if (!ctx) return null;

    // Draw un-mirrored original frame for backend InsightFace inference
    ctx.drawImage(video, 0, 0, captureCanvas.width, captureCanvas.height);
    return captureCanvas.toDataURL('image/jpeg', 0.95);
  }, []);

  useEffect(() => {
    onCaptureFrameReady(getFrameDataUrl);
  }, [getFrameDataUrl, onCaptureFrameReady]);

  // 1. Initialize MediaPipe FaceLandmarker
  useEffect(() => {
    let isMounted = true;

    const initMediaPipe = async () => {
      try {
        setModelLoading(true);
        setModelError(null);

        const filesetResolver = await FilesetResolver.forVisionTasks(
          'https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.18/wasm'
        );

        if (!isMounted) return;

        const landmarker = await FaceLandmarker.createFromOptions(filesetResolver, {
          baseOptions: {
            modelAssetPath:
              'https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task',
            delegate: 'GPU',
          },
          runningMode: 'VIDEO',
          numFaces: 2,
          minFaceDetectionConfidence: 0.5,
          minFacePresenceConfidence: 0.5,
          minTrackingConfidence: 0.5,
          outputFaceBlendshapes: false,
          outputFacialTransformationMatrixes: false,
        });

        if (!isMounted) {
          landmarker.close();
          return;
        }

        landmarkerRef.current = landmarker;
        setModelLoading(false);
      } catch (err: any) {
        console.warn('Failed to load MediaPipe Face Landmarker:', err);
        if (isMounted) {
          setModelError(
            err.message || 'Could not load real-time face detection model. Check network connectivity.'
          );
          setModelLoading(false);
        }
      }
    };

    initMediaPipe();

    return () => {
      isMounted = false;
      if (landmarkerRef.current) {
        try {
          landmarkerRef.current.close();
        } catch {}
        landmarkerRef.current = null;
      }
    };
  }, []);

  // 2. Start Camera
  useEffect(() => {
    let isMounted = true;

    const startCamera = async () => {
      try {
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
          throw new Error('WebRTC camera is not supported by your browser.');
        }

        const stream = await navigator.mediaDevices.getUserMedia({
          video: {
            width: { ideal: 1280 },
            height: { ideal: 720 },
            facingMode: 'user',
          },
          audio: false,
        });

        if (!isMounted) {
          stream.getTracks().forEach((t) => t.stop());
          return;
        }

        streamRef.current = stream;
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
          await videoRef.current.play();
          setCameraStarted(true);
        }
      } catch (err: any) {
        console.warn('Camera stream error:', err);
        if (isMounted) {
          onCameraError(
            err.name === 'NotAllowedError'
              ? 'Camera permission denied. Please allow camera access in browser permissions.'
              : err.message || 'Unable to access camera.'
          );
        }
      }
    };

    startCamera();

    return () => {
      isMounted = false;
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((t) => t.stop());
        streamRef.current = null;
      }
    };
  }, [onCameraError]);

  // 3. Real-Time Detection & Rendering Loop
  useEffect(() => {
    let isRunning = true;

    const processLoop = () => {
      if (!isRunning) return;

      const video = videoRef.current;
      const canvas = canvasRef.current;
      const landmarker = landmarkerRef.current;

      if (video && canvas && landmarker && video.readyState >= 2) {
        const videoWidth = video.videoWidth;
        const videoHeight = video.videoHeight;

        if (canvas.width !== videoWidth || canvas.height !== videoHeight) {
          canvas.width = videoWidth;
          canvas.height = videoHeight;
        }

        const ctx = canvas.getContext('2d');
        if (ctx) {
          ctx.clearRect(0, 0, canvas.width, canvas.height);

          const timestamp = performance.now();
          const results = landmarker.detectForVideo(video, timestamp);

          const faceCount = results.faceLandmarks ? results.faceLandmarks.length : 0;

          if (faceCount === 0) {
            drawAlignmentGuide(ctx, canvas.width, canvas.height, 'neutral', isCapturing);
            onStatusChange({
              faceCount: 0,
              isAligned: false,
              isPoseMatched: false,
              currentEstimatedPose: 'UNKNOWN',
              liveYawAngle: 0,
              livePitchAngle: 0,
              statusMessage: 'Position your face in the center frame',
              isReadyToCapture: false,
            });
          } else if (faceCount > 1) {
            drawAlignmentGuide(ctx, canvas.width, canvas.height, 'warning', isCapturing);
            onStatusChange({
              faceCount,
              isAligned: false,
              isPoseMatched: false,
              currentEstimatedPose: 'UNKNOWN',
              liveYawAngle: 0,
              livePitchAngle: 0,
              statusMessage: 'Multiple faces detected — only 1 person allowed',
              isReadyToCapture: false,
            });
          } else {
            const landmarks = results.faceLandmarks[0];
            const metrics = analyzeFaceLandmarks(landmarks, canvas.width, canvas.height, targetPose);

            drawLandmarksOverlay(ctx, landmarks, canvas.width, canvas.height, metrics.isPoseMatched);
            drawBoundingBox(ctx, metrics.bbox, metrics.isPoseMatched);
            drawAlignmentGuide(
              ctx,
              canvas.width,
              canvas.height,
              metrics.isAligned && metrics.isPoseMatched ? 'ready' : metrics.isAligned ? 'aligning' : 'warning',
              isCapturing
            );

            let statusMessage = '';
            if (!metrics.isAligned) {
              statusMessage = metrics.alignmentHint;
            } else if (!metrics.isPoseMatched) {
              statusMessage = `Adjust pose: ${targetPoseLabel}`;
            } else {
              statusMessage = 'Hold steady — Ready to capture';
            }

            onStatusChange({
              faceCount: 1,
              isAligned: metrics.isAligned,
              isPoseMatched: metrics.isPoseMatched,
              currentEstimatedPose: metrics.estimatedPose,
              liveYawAngle: Math.round(metrics.yawAngle),
              livePitchAngle: Math.round(metrics.pitchAngle),
              statusMessage,
              isReadyToCapture: metrics.isAligned && metrics.isPoseMatched && !isCapturing,
            });
          }
        }
      }

      animFrameIdRef.current = requestAnimationFrame(processLoop);
    };

    if (cameraStarted && !modelLoading) {
      animFrameIdRef.current = requestAnimationFrame(processLoop);
    }

    return () => {
      isRunning = false;
      if (animFrameIdRef.current) {
        cancelAnimationFrame(animFrameIdRef.current);
        animFrameIdRef.current = null;
      }
    };
  }, [cameraStarted, modelLoading, targetPose, targetPoseLabel, isCapturing, onStatusChange]);

  return (
    <Box
      sx={{
        position: 'relative',
        width: '100%',
        height: '100%',
        bgcolor: '#0B0F19',
        overflow: 'hidden',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
      }}
    >
      {/* Live Video Feed */}
      <video
        ref={videoRef}
        playsInline
        muted
        autoPlay
        style={{
          width: '100%',
          height: '100%',
          objectFit: 'cover',
          transform: 'scaleX(-1)', // Mirror mode for natural self-alignment
        }}
      />

      {/* Overlaid Canvas for Real-Time Landmark Mesh & Reticle */}
      <canvas
        ref={canvasRef}
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          width: '100%',
          height: '100%',
          objectFit: 'cover',
          transform: 'scaleX(-1)', // Match video mirror
          pointerEvents: 'none',
        }}
      />

      {/* Model Loading State */}
      {modelLoading && (
        <Box
          sx={{
            position: 'absolute',
            inset: 0,
            bgcolor: 'rgba(11, 15, 25, 0.85)',
            backdropFilter: 'blur(6px)',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            gap: 2,
            zIndex: 10,
          }}
        >
          <CircularProgress size={44} sx={{ color: '#38BDF8' }} />
          <Typography variant="body2" sx={{ color: '#F1F5F9', fontWeight: 600 }}>
            Initializing MediaPipe Neural Face Detector...
          </Typography>
        </Box>
      )}

      {/* Model Error State */}
      {modelError && (
        <Box
          sx={{
            position: 'absolute',
            inset: 0,
            bgcolor: 'rgba(11, 15, 25, 0.9)',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            p: 3,
            zIndex: 10,
          }}
        >
          <Chip label="Vision Engine Offline" color="error" sx={{ mb: 1.5, fontWeight: 700 }} />
          <Typography variant="body2" sx={{ color: '#FDA4AF', textAlign: 'center' }}>
            {modelError}
          </Typography>
        </Box>
      )}
    </Box>
  );
};

// ==============================================================================
// Face Landmark Analysis & Pose Estimation Engine
// ==============================================================================

interface BoundingBox {
  minX: number;
  minY: number;
  maxX: number;
  maxY: number;
  width: number;
  height: number;
  centerX: number;
  centerY: number;
}

function analyzeFaceLandmarks(
  landmarks: NormalizedLandmark[],
  canvasWidth: number,
  canvasHeight: number,
  targetPose: 'FRONT' | 'LEFT' | 'RIGHT' | 'UP' | 'DOWN'
) {
  let minX = 1;
  let minY = 1;
  let maxX = 0;
  let maxY = 0;

  for (let i = 0; i < landmarks.length; i++) {
    const lm = landmarks[i];
    if (lm.x < minX) minX = lm.x;
    if (lm.x > maxX) maxX = lm.x;
    if (lm.y < minY) minY = lm.y;
    if (lm.y > maxY) maxY = lm.y;
  }

  const bbox: BoundingBox = {
    minX: minX * canvasWidth,
    minY: minY * canvasHeight,
    maxX: maxX * canvasWidth,
    maxY: maxY * canvasHeight,
    width: (maxX - minX) * canvasWidth,
    height: (maxY - minY) * canvasHeight,
    centerX: ((minX + maxX) / 2) * canvasWidth,
    centerY: ((minY + maxY) / 2) * canvasHeight,
  };

  // Center alignment check
  const normCenterX = (minX + maxX) / 2;
  const normCenterY = (minY + maxY) / 2;
  const normWidth = maxX - minX;

  let isAligned = true;
  let alignmentHint = 'Face aligned';

  if (normWidth < 0.18) {
    isAligned = false;
    alignmentHint = 'Move closer to the camera';
  } else if (normWidth > 0.70) {
    isAligned = false;
    alignmentHint = 'Move slightly back';
  } else if (normCenterX < 0.28) {
    isAligned = false;
    alignmentHint = 'Move towards center';
  } else if (normCenterX > 0.72) {
    isAligned = false;
    alignmentHint = 'Move towards center';
  } else if (normCenterY < 0.20) {
    isAligned = false;
    alignmentHint = 'Lower camera or head slightly';
  } else if (normCenterY > 0.80) {
    isAligned = false;
    alignmentHint = 'Raise camera or head slightly';
  }

  // Head Pose Estimation from MediaPipe Landmarks:
  // Key points: Nose tip (#1), Left cheek tragus (#234), Right cheek tragus (#454), Forehead (#10), Chin (#152)
  const nose = landmarks[1];
  const leftCheek = landmarks[234];
  const rightCheek = landmarks[454];
  const forehead = landmarks[10];
  const chin = landmarks[152];

  // In un-mirrored normalized space:
  // Left cheek is x < nose.x, Right cheek is x > nose.x
  const distLeft = Math.abs(nose.x - leftCheek.x);
  const distRight = Math.abs(rightCheek.x - nose.x);
  const totalHoriz = distLeft + distRight;

  const yawRatio = totalHoriz > 0 ? distLeft / totalHoriz : 0.5;
  // yawAngle in degrees (0 = front, negative = turned right, positive = turned left from subject perspective)
  const yawAngle = (yawRatio - 0.5) * 90;

  // Vertical pitch ratio:
  const distForehead = Math.abs(nose.y - forehead.y);
  const distChin = Math.abs(chin.y - nose.y);
  const totalVert = distForehead + distChin;

  const pitchRatio = totalVert > 0 ? distForehead / totalVert : 0.5;
  // pitchAngle in degrees (0 = front, positive = looking up, negative = looking down)
  const pitchAngle = (0.55 - pitchRatio) * 100;

  // Determine current estimated pose
  let estimatedPose: 'FRONT' | 'LEFT' | 'RIGHT' | 'UP' | 'DOWN' = 'FRONT';

  if (yawAngle > 14) {
    estimatedPose = 'LEFT';
  } else if (yawAngle < -14) {
    estimatedPose = 'RIGHT';
  } else if (pitchAngle > 10) {
    estimatedPose = 'UP';
  } else if (pitchAngle < -10) {
    estimatedPose = 'DOWN';
  } else {
    estimatedPose = 'FRONT';
  }

  // Check if current estimated pose satisfies targetPose
  let isPoseMatched = false;

  switch (targetPose) {
    case 'FRONT':
      isPoseMatched = Math.abs(yawAngle) <= 13 && Math.abs(pitchAngle) <= 13;
      break;
    case 'LEFT':
      // User turned head to their left
      isPoseMatched = yawAngle >= 12;
      break;
    case 'RIGHT':
      // User turned head to their right
      isPoseMatched = yawAngle <= -12;
      break;
    case 'UP':
      // User tilted head upward
      isPoseMatched = pitchAngle >= 9;
      break;
    case 'DOWN':
      // User tilted head downward
      isPoseMatched = pitchAngle <= -9;
      break;
  }

  return {
    bbox,
    isAligned,
    alignmentHint,
    yawAngle,
    pitchAngle,
    estimatedPose,
    isPoseMatched,
  };
}

// ==============================================================================
// Canvas Drawing Utilities
// ==============================================================================

// Important contour landmark indices for futuristic face mesh rendering
const OVAL_INDICES = [
  10, 338, 297, 332, 284, 251, 389, 356, 454, 323, 361, 288, 397, 365, 379, 378,
  400, 377, 152, 148, 176, 149, 150, 136, 172, 58, 132, 93, 234, 127, 162, 21,
  54, 103, 67, 109,
];

const LEFT_EYE_INDICES = [33, 160, 158, 133, 153, 144, 33];
const RIGHT_EYE_INDICES = [263, 387, 385, 362, 380, 373, 263];
const LIPS_INDICES = [61, 185, 40, 39, 37, 0, 267, 269, 270, 409, 291, 375, 321, 405, 314, 17, 84, 181, 91, 146, 61];

function drawLandmarksOverlay(
  ctx: CanvasRenderingContext2D,
  landmarks: NormalizedLandmark[],
  width: number,
  height: number,
  isMatched: boolean
) {
  const dotColor = isMatched ? 'rgba(16, 185, 129, 0.7)' : 'rgba(56, 189, 248, 0.6)';
  const contourColor = isMatched ? 'rgba(16, 185, 129, 0.4)' : 'rgba(99, 102, 241, 0.35)';

  // Draw face contours
  drawContour(ctx, landmarks, OVAL_INDICES, width, height, contourColor, 1.5);
  drawContour(ctx, landmarks, LEFT_EYE_INDICES, width, height, contourColor, 1.2);
  drawContour(ctx, landmarks, RIGHT_EYE_INDICES, width, height, contourColor, 1.2);
  drawContour(ctx, landmarks, LIPS_INDICES, width, height, contourColor, 1.2);

  // Draw key landmark points with subtle glow
  ctx.fillStyle = dotColor;
  for (let i = 0; i < landmarks.length; i += 4) {
    const lm = landmarks[i];
    const x = lm.x * width;
    const y = lm.y * height;
    ctx.beginPath();
    ctx.arc(x, y, 1.4, 0, 2 * Math.PI);
    ctx.fill();
  }
}

function drawContour(
  ctx: CanvasRenderingContext2D,
  landmarks: NormalizedLandmark[],
  indices: number[],
  width: number,
  height: number,
  color: string,
  lineWidth: number
) {
  if (indices.length === 0) return;
  ctx.strokeStyle = color;
  ctx.lineWidth = lineWidth;
  ctx.beginPath();

  const first = landmarks[indices[0]];
  ctx.moveTo(first.x * width, first.y * height);

  for (let i = 1; i < indices.length; i++) {
    const lm = landmarks[indices[i]];
    ctx.lineTo(lm.x * width, lm.y * height);
  }

  ctx.stroke();
}

function drawBoundingBox(ctx: CanvasRenderingContext2D, bbox: BoundingBox, isMatched: boolean) {
  const cornerLength = Math.min(bbox.width, bbox.height) * 0.18;
  const color = isMatched ? '#10B981' : '#38BDF8';

  ctx.strokeStyle = color;
  ctx.lineWidth = 2.5;

  const { minX, minY, maxX, maxY } = bbox;

  // Top-Left corner
  ctx.beginPath();
  ctx.moveTo(minX, minY + cornerLength);
  ctx.lineTo(minX, minY);
  ctx.lineTo(minX + cornerLength, minY);
  ctx.stroke();

  // Top-Right corner
  ctx.beginPath();
  ctx.moveTo(maxX - cornerLength, minY);
  ctx.lineTo(maxX, minY);
  ctx.lineTo(maxX, minY + cornerLength);
  ctx.stroke();

  // Bottom-Left corner
  ctx.beginPath();
  ctx.moveTo(minX, maxY - cornerLength);
  ctx.lineTo(minX, maxY);
  ctx.lineTo(minX + cornerLength, maxY);
  ctx.stroke();

  // Bottom-Right corner
  ctx.beginPath();
  ctx.moveTo(maxX - cornerLength, maxY);
  ctx.lineTo(maxX, maxY);
  ctx.lineTo(maxX, maxY - cornerLength);
  ctx.stroke();
}

function drawAlignmentGuide(
  ctx: CanvasRenderingContext2D,
  width: number,
  height: number,
  state: 'neutral' | 'aligning' | 'ready' | 'warning',
  isCapturing: boolean
) {
  const centerX = width / 2;
  const centerY = height / 2;
  const radiusX = width * 0.22;
  const radiusY = height * 0.36;

  ctx.save();

  let strokeColor = 'rgba(99, 102, 241, 0.4)';
  let isDashed = true;
  let shadowColor = 'transparent';

  if (isCapturing) {
    strokeColor = '#10B981';
    isDashed = false;
    shadowColor = 'rgba(16, 185, 129, 0.8)';
  } else if (state === 'ready') {
    strokeColor = '#10B981';
    isDashed = false;
    shadowColor = 'rgba(16, 185, 129, 0.5)';
  } else if (state === 'aligning') {
    strokeColor = '#38BDF8';
    isDashed = false;
    shadowColor = 'rgba(56, 189, 248, 0.3)';
  } else if (state === 'warning') {
    strokeColor = '#F59E0B';
    isDashed = true;
    shadowColor = 'rgba(245, 158, 11, 0.4)';
  }

  ctx.strokeStyle = strokeColor;
  ctx.lineWidth = state === 'ready' || isCapturing ? 3 : 2;
  if (isDashed) {
    ctx.setLineDash([8, 6]);
  } else {
    ctx.setLineDash([]);
  }

  if (shadowColor !== 'transparent') {
    ctx.shadowColor = shadowColor;
    ctx.shadowBlur = 16;
  }

  ctx.beginPath();
  ctx.ellipse(centerX, centerY, radiusX, radiusY, 0, 0, 2 * Math.PI);
  ctx.stroke();

  ctx.restore();
}
