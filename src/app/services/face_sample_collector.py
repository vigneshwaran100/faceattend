from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class FaceSample:
    embedding: np.ndarray


class FaceSampleCollector:
    def __init__(
        self,
        target_samples: int = 10,
        duplicate_threshold: float = 0.98,
    ) -> None:
        self._target_samples = target_samples
        self._duplicate_threshold = duplicate_threshold
        self._samples: list[FaceSample] = []

    @property
    def samples(self) -> list[FaceSample]:
        return list(self._samples)

    @property
    def is_complete(self) -> bool:
        return len(self._samples) >= self._target_samples

    def add(self, embedding: np.ndarray) -> bool:
        normalized_embedding = self._normalize(embedding)

        if self._is_duplicate(normalized_embedding):
            return False

        if self.is_complete:
            return False

        self._samples.append(
            FaceSample(
                embedding=normalized_embedding,
            )
        )

        return True

    def reset(self) -> None:
        self._samples.clear()

    def _is_duplicate(self, embedding: np.ndarray) -> bool:
        return any(
            self._cosine_similarity(
                embedding,
                sample.embedding,
            )
            >= self._duplicate_threshold
            for sample in self._samples
        )

    @staticmethod
    def _normalize(embedding: np.ndarray) -> np.ndarray:
        norm = np.linalg.norm(embedding)

        if norm == 0:
            raise ValueError("Cannot normalize a zero embedding")

        return embedding / norm

    @staticmethod
    def _cosine_similarity(
        first: np.ndarray,
        second: np.ndarray,
    ) -> float:
        return float(np.dot(first, second))