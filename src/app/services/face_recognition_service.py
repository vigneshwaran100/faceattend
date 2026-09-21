from dataclasses import dataclass

import numpy as np

from app.infrastructure.milvus_v2_repository import (
    MilvusV2Repository,
)


@dataclass(frozen=True)
class RecognitionResult:
    employee_id: str | None
    similarity: float
    recognized: bool


class FaceRecognitionService:
    def __init__(
        self,
        repository: MilvusV2Repository,
        threshold: float = 0.60,
    ) -> None:
        self._repository = repository
        self._threshold = threshold

    def recognize(
        self,
        embedding: np.ndarray,
    ) -> RecognitionResult:
        vector = self._normalize(embedding)

        results = self._repository.search_embedding(
            vector.tolist(),
            limit=1,
        )

        if not results:
            return RecognitionResult(
                employee_id=None,
                similarity=0.0,
                recognized=False,
            )

        best_match = results[0]

        similarity = float(
            best_match["distance"]
        )

        if similarity < self._threshold:
            return RecognitionResult(
                employee_id=None,
                similarity=similarity,
                recognized=False,
            )

        return RecognitionResult(
            employee_id=best_match["employee_id"],
            similarity=similarity,
            recognized=True,
        )

    @staticmethod
    def _normalize(
        embedding: np.ndarray,
    ) -> np.ndarray:
        norm = np.linalg.norm(embedding)

        if norm == 0:
            raise ValueError(
                "Cannot recognize using a zero embedding"
            )

        return embedding / norm