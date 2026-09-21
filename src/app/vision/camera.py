import time
import logging
import cv2
import numpy as np

from app.core.config import settings

logger = logging.getLogger(__name__)


class CameraError(RuntimeError):
    """Raised when the camera cannot be initialized or read."""


class Camera:
    def __init__(self, camera_index: int | None = None) -> None:
        self._camera_index = (
            settings.camera_index if camera_index is None else camera_index
        )
        self._capture: cv2.VideoCapture | None = None

    def start(self) -> None:
        if self._capture is not None:
            return

        logger.debug("Starting camera with index %s", self._camera_index)

        # On Windows, DirectShow (CAP_DSHOW) provides reliable frame capture and avoids MSMF stream drops
        capture = cv2.VideoCapture(self._camera_index, cv2.CAP_DSHOW)

        if not capture.isOpened():
            capture.release()
            capture = cv2.VideoCapture(self._camera_index)

        if not capture.isOpened():
            capture.release()
            logger.error(
                "Unable to open camera with index %s", self._camera_index
            )
            raise CameraError(
                f"Unable to open camera with index {self._camera_index}"
            )

        self._capture = capture

    def read(self, max_retries: int = 5) -> np.ndarray:
        if self._capture is None:
            raise CameraError("Camera has not been started")

        for attempt in range(max_retries):
            success, frame = self._capture.read()
            if success and frame is not None and frame.size > 0:
                return frame

            time.sleep(0.05)

        raise CameraError("Failed to read frame from camera")

    def stop(self) -> None:
        if self._capture is not None:
            self._capture.release()
            self._capture = None
            logger.debug("Camera stopped | index=%s", self._camera_index)

    def __enter__(self) -> "Camera":
        self.start()
        return self

    def __exit__(self, *args: object) -> None:
        self.stop()