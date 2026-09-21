import cv2
import numpy as np

from app.models.face import FaceDetection
from app.services.face_quality_service import FaceQualityService


def create_detection(
    confidence: float = 0.95,
    box: tuple[int, int, int, int] = (50, 50, 250, 250),
) -> FaceDetection:
    return FaceDetection(
        bounding_box=box,
        confidence=confidence,
    )


def create_sharp_frame() -> np.ndarray:
    frame = np.zeros((300, 300, 3), dtype=np.uint8)

    # Create edges/details so Laplacian variance is high.
    cv2.rectangle(
        frame,
        (70, 70),
        (230, 230),
        (255, 255, 255),
        5,
    )

    return frame


def create_blurry_frame() -> np.ndarray:
    frame = create_sharp_frame()

    return cv2.GaussianBlur(
        frame,
        (51, 51),
        0,
    )


def test_accepts_good_face() -> None:
    service = FaceQualityService(
        min_confidence=0.80,
        min_face_size=80,
        min_blur_score=10.0,
    )

    frame = create_sharp_frame()
    detection = create_detection()

    assert service.is_acceptable(frame, detection) is True


def test_rejects_low_confidence() -> None:
    service = FaceQualityService()

    frame = create_sharp_frame()
    detection = create_detection(confidence=0.50)

    assert service.is_acceptable(frame, detection) is False


def test_rejects_small_face() -> None:
    service = FaceQualityService()

    frame = create_sharp_frame()
    detection = create_detection(
        box=(50, 50, 100, 100),
    )

    assert service.is_acceptable(frame, detection) is False


def test_rejects_blurry_face() -> None:
    service = FaceQualityService(
        min_blur_score=100.0,
    )

    frame = create_blurry_frame()
    detection = create_detection()

    assert service.is_acceptable(frame, detection) is False