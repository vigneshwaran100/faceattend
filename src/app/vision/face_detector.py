from dataclasses import dataclass

import numpy as np
from insightface.app import FaceAnalysis


@dataclass(frozen=True)
class FaceDetection:
    bounding_box: tuple[int, int, int, int]
    confidence: float


class FaceDetector:
    # def __init__(self) -> None:
    #     self._model = FaceAnalysis(
    #         name="buffalo_l",
    #         providers=["CPUExecutionProvider"],
    #     )

    #     self._model.prepare(
    #         ctx_id=0,
    #         det_size=(640, 640),
    #     )
    def __init__(self, model: FaceAnalysis) -> None:
        self._model = model

    def detect(self, frame: np.ndarray) -> list[FaceDetection]:
        faces = self._model.get(frame)

        return [
            FaceDetection(
                bounding_box=tuple(
                    int(value) for value in face.bbox
                ),
                confidence=float(face.det_score),
            )
            for face in faces
        ]