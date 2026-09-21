from dataclasses import dataclass
import logging

import cv2
import numpy as np

from app.models.face import FaceDetection

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class FaceQualityResult:
    acceptable: bool
    reason: str | None = None
    confidence: float = 0.0
    width: int = 0
    height: int = 0
    blur_score: float = 0.0
    min_confidence: float = 0.70
    min_face_size: int = 80
    min_blur_score: float = 100.0

    @property
    def details(self) -> str:
        if self.acceptable:
            return "Face quality acceptable"
        if self.reason == "confidence":
            return (
                f"reason=confidence | "
                f"confidence={self.confidence:.3f} (min={self.min_confidence:.2f})"
            )
        if self.reason == "face_size":
            return (
                f"reason=face_size | "
                f"width={self.width} | height={self.height} "
                f"(min={self.min_face_size}px)"
            )
        if self.reason == "blur":
            return (
                f"reason=blur | "
                f"score={self.blur_score:.2f} (min={self.min_blur_score:.2f})"
            )
        if self.reason == "empty_crop":
            return "reason=empty_crop"
        return f"reason={self.reason}"


class FaceQualityService:
    def __init__(
        self,
        min_confidence: float = 0.70,
        min_face_size: int = 80,
        min_blur_score: float = 100.0,
    ) -> None:
        self._min_confidence = min_confidence
        self._min_face_size = min_face_size
        self._min_blur_score = min_blur_score

    @property
    def min_confidence(self) -> float:
        return self._min_confidence

    @property
    def min_face_size(self) -> int:
        return self._min_face_size

    @property
    def min_blur_score(self) -> float:
        return self._min_blur_score

    def check_quality(
        self,
        frame: np.ndarray,
        detection: FaceDetection,
    ) -> FaceQualityResult:
        x1, y1, x2, y2 = detection.bounding_box
        width = x2 - x1
        height = y2 - y1

        if detection.confidence < self._min_confidence:
            return FaceQualityResult(
                acceptable=False,
                reason="confidence",
                confidence=detection.confidence,
                width=width,
                height=height,
                min_confidence=self._min_confidence,
                min_face_size=self._min_face_size,
                min_blur_score=self._min_blur_score,
            )

        if width < self._min_face_size or height < self._min_face_size:
            return FaceQualityResult(
                acceptable=False,
                reason="face_size",
                confidence=detection.confidence,
                width=width,
                height=height,
                min_confidence=self._min_confidence,
                min_face_size=self._min_face_size,
                min_blur_score=self._min_blur_score,
            )

        face_crop = frame[y1:y2, x1:x2]

        if face_crop.size == 0:
            return FaceQualityResult(
                acceptable=False,
                reason="empty_crop",
                confidence=detection.confidence,
                width=width,
                height=height,
                min_confidence=self._min_confidence,
                min_face_size=self._min_face_size,
                min_blur_score=self._min_blur_score,
            )

        gray = cv2.cvtColor(face_crop, cv2.COLOR_BGR2GRAY)

        blur_score = float(
            cv2.Laplacian(
                gray,
                cv2.CV_64F,
            ).var()
        )

        if blur_score < self._min_blur_score:
            return FaceQualityResult(
                acceptable=False,
                reason="blur",
                confidence=detection.confidence,
                width=width,
                height=height,
                blur_score=blur_score,
                min_confidence=self._min_confidence,
                min_face_size=self._min_face_size,
                min_blur_score=self._min_blur_score,
            )

        return FaceQualityResult(
            acceptable=True,
            confidence=detection.confidence,
            width=width,
            height=height,
            blur_score=blur_score,
            min_confidence=self._min_confidence,
            min_face_size=self._min_face_size,
            min_blur_score=self._min_blur_score,
        )

    def is_acceptable(
        self,
        frame: np.ndarray,
        detection: FaceDetection,
    ) -> bool:
        return self.check_quality(frame, detection).acceptable