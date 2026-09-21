import numpy as np
import pytest

from app.services.face_sample_collector import FaceSampleCollector


def test_first_embedding_is_accepted() -> None:
    collector = FaceSampleCollector(target_samples=3)

    embedding = np.array([1.0, 0.0, 0.0])

    assert collector.add(embedding) is True
    assert len(collector.samples) == 1


def test_duplicate_embedding_is_rejected() -> None:
    collector = FaceSampleCollector(
        target_samples=3,
        duplicate_threshold=0.98,
    )

    embedding = np.array([1.0, 0.0, 0.0])

    assert collector.add(embedding) is True
    assert collector.add(embedding) is False

    assert len(collector.samples) == 1


def test_different_embedding_is_accepted() -> None:
    collector = FaceSampleCollector(
        target_samples=3,
        duplicate_threshold=0.98,
    )

    first = np.array([1.0, 0.0, 0.0])
    second = np.array([0.0, 1.0, 0.0])

    assert collector.add(first) is True
    assert collector.add(second) is True

    assert len(collector.samples) == 2


def test_collector_stops_at_target() -> None:
    collector = FaceSampleCollector(target_samples=2)

    first = np.array([1.0, 0.0, 0.0])
    second = np.array([0.0, 1.0, 0.0])
    third = np.array([0.0, 0.0, 1.0])

    assert collector.add(first) is True
    assert collector.add(second) is True

    assert collector.is_complete is True
    assert collector.add(third) is False

    assert len(collector.samples) == 2


def test_zero_embedding_is_rejected() -> None:
    collector = FaceSampleCollector()

    zero_embedding = np.zeros(3)

    with pytest.raises(ValueError, match="zero embedding"):
        collector.add(zero_embedding)