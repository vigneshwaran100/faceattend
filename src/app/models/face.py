from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class FaceDetection:
    bounding_box: tuple[int, int, int, int]
    confidence: float
    landmarks: np.ndarray | None = None
    pose: tuple[float, float, float] | None = None


@dataclass(frozen=True)
class FaceEmbedding:
    vector: np.ndarray

@dataclass(frozen=True)
class FaceResult:
    bounding_box: tuple[int, int, int, int]
    confidence: float
    embedding: np.ndarray