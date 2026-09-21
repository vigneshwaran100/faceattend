import numpy as np
import pytest
from unittest.mock import Mock

from app.services.face_recognition_service import (
    FaceRecognitionService,
)


def create_service() -> tuple[
    FaceRecognitionService,
    Mock,
]:
    repository = Mock()

    service = FaceRecognitionService(
        repository=repository,
        threshold=0.60,
    )

    return service, repository


def test_recognizes_matching_employee() -> None:
    service, repository = create_service()

    repository.search_embedding.return_value = [
        {
            "vector_id": 1001,
            "employee_id": "EMP001",
            "distance": 0.92,
            "model_name": "w600k_r50",
            "model_version": "buffalo_l",
            "embedding_version": "1",
            "created_at": 1234567890,
        }
    ]

    embedding = np.zeros(512, dtype=np.float32)
    embedding[0] = 1.0

    result = service.recognize(embedding)

    assert result.recognized is True
    assert result.employee_id == "EMP001"
    assert result.similarity == 0.92


def test_rejects_low_similarity() -> None:
    service, repository = create_service()

    repository.search_embedding.return_value = [
        {
            "vector_id": 1001,
            "employee_id": "EMP001",
            "distance": 0.45,
            "model_name": "w600k_r50",
            "model_version": "buffalo_l",
            "embedding_version": "1",
            "created_at": 1234567890,
        }
    ]

    embedding = np.zeros(512, dtype=np.float32)
    embedding[0] = 1.0

    result = service.recognize(embedding)

    assert result.recognized is False
    assert result.employee_id is None
    assert result.similarity == 0.45


def test_returns_unknown_when_no_match() -> None:
    service, repository = create_service()

    repository.search_embedding.return_value = []

    embedding = np.zeros(512, dtype=np.float32)
    embedding[0] = 1.0

    result = service.recognize(embedding)

    assert result.recognized is False
    assert result.employee_id is None
    assert result.similarity == 0.0


def test_rejects_zero_embedding() -> None:
    service, _ = create_service()

    embedding = np.zeros(
        512,
        dtype=np.float32,
    )

    with pytest.raises(
        ValueError,
        match="zero embedding",
    ):
        service.recognize(embedding)


def test_normalizes_embedding_before_search() -> None:
    service, repository = create_service()

    repository.search_embedding.return_value = []

    embedding = np.zeros(
        512,
        dtype=np.float32,
    )

    embedding[0] = 5.0

    service.recognize(embedding)

    searched_vector = (
        repository.search_embedding
        .call_args.args[0]
    )

    assert np.isclose(
        np.linalg.norm(searched_vector),
        1.0,
    )