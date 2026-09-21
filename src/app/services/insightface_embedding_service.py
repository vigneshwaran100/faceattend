import numpy as np
from insightface.app import FaceAnalysis

from app.services.embedding_service import EmbeddingService


class InsightFaceEmbeddingService(EmbeddingService):
    def __init__(self, model: FaceAnalysis) -> None:
        self._model = model

    def generate(self, face: object) -> np.ndarray:
        embedding = getattr(face, "embedding", None)

        if embedding is None:
            raise ValueError("Face embedding is not available")

        return np.asarray(embedding, dtype=np.float32)