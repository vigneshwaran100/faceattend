from abc import ABC, abstractmethod

import numpy as np


class EmbeddingService(ABC):
    @abstractmethod
    def generate(self, face: object) -> np.ndarray:
        """Generate an embedding for a detected face."""
        raise NotImplementedError