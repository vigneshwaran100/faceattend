import numpy as np
from insightface.app import FaceAnalysis

from app.models.face import FaceDetection, FaceEmbedding


class FaceEngine:
    def __init__(self, model: FaceAnalysis) -> None:
        self._model = model

    def process(
        self,
        frame: np.ndarray,
    ) -> tuple[list[FaceDetection], list[FaceEmbedding]]:

        faces = self._model.get(frame)

        detections: list[FaceDetection] = []
        embeddings: list[FaceEmbedding] = []

        for face in faces:
            landmarks = getattr(face, "kps", None)
            pose_raw = getattr(face, "pose", None)
            pose = (
                tuple(float(v) for v in pose_raw)
                if isinstance(pose_raw, (list, tuple, np.ndarray))
                and len(pose_raw) >= 3
                else None
            )

            detection = FaceDetection(
                bounding_box=tuple(
                    int(value) for value in face.bbox
                ),
                confidence=float(face.det_score),
                landmarks=landmarks,
                pose=pose,
            )

            embedding = FaceEmbedding(
                vector=np.asarray(
                    face.embedding,
                    dtype=np.float32,
                ),
            )

            detections.append(detection)
            embeddings.append(embedding)

        return detections, embeddings