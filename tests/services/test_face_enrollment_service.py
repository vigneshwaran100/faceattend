from datetime import datetime, timezone
from unittest.mock import Mock

import numpy as np
import pytest

from app.models.employee import Employee
from app.services.face_enrollment_service import (
    FaceEnrollmentService,
)
from app.services.face_sample_collector import (
    FaceSampleCollector,
)


def create_employee() -> Employee:
    now = datetime.now(timezone.utc)

    return Employee(
        employee_id="EMP001",
        name="Vigneshwaran",
        email="v@example.com",
        team_id="TEAM001",
        department_id="DEPT001",
        designation="Software Engineer",
        status="active",
        created_at=now,
        updated_at=now,
    )


def create_service() -> tuple[
    FaceEnrollmentService,
    Mock,
    Mock,
    Mock,
]:
    face_engine = Mock()
    quality_service = Mock()
    milvus_repository = Mock()

    milvus_repository.get_employee_embeddings.return_value = []

    service = FaceEnrollmentService(
        face_engine=face_engine,
        quality_service=quality_service,
        milvus_repository=milvus_repository,
    )

    return (
        service,
        face_engine,
        quality_service,
        milvus_repository,
    )
def test_create_collector() -> None:
    service, _, _, _ = create_service()

    collector = service.create_collector()

    assert isinstance(
        collector,
        FaceSampleCollector,
    )

    assert collector.is_complete is False


def test_process_frame_accepts_good_face() -> None:
    service, face_engine, quality_service, _ = (
        create_service()
    )

    detection = Mock()
    embedding = Mock()

    embedding.vector = np.ones(512, dtype=np.float32)

    face_engine.process.return_value = (
        [detection],
        [embedding],
    )

    quality_service.is_acceptable.return_value = True

    collector = service.create_collector()

    frame = np.zeros(
        (480, 640, 3),
        dtype=np.uint8,
    )

    detections = service.process_frame(
        frame,
        collector,
    )

    assert detections == [detection]
    assert len(collector.samples) == 1

    quality_service.is_acceptable.assert_called_once_with(
        frame,
        detection,
    )


def test_process_frame_rejects_bad_face() -> None:
    service, face_engine, quality_service, _ = (
        create_service()
    )

    detection = Mock()
    embedding = Mock()

    embedding.vector = np.ones(512, dtype=np.float32)

    face_engine.process.return_value = (
        [detection],
        [embedding],
    )

    quality_service.is_acceptable.return_value = False

    collector = service.create_collector()

    frame = np.zeros(
        (480, 640, 3),
        dtype=np.uint8,
    )

    service.process_frame(
        frame,
        collector,
    )

    assert len(collector.samples) == 0


def test_save_samples_requires_complete_enrollment() -> None:
    service, _, _, milvus_repository = (
        create_service()
    )

    collector = service.create_collector()
    employee = create_employee()

    with pytest.raises(
        ValueError,
        match="Face enrollment is incomplete",
    ):
        service.save_samples(
            employee,
            collector,
        )

    milvus_repository.insert_embedding.assert_not_called()


def test_save_samples_stores_all_embeddings() -> None:
    service, _, _, milvus_repository = (
        create_service()
    )

    collector = service.create_collector()
    employee = create_employee()

    for index in range(10):
        embedding = np.zeros(
            512,
            dtype=np.float32,
        )

        embedding[index] = 1.0

        collector.add(embedding)

    assert collector.is_complete is True

    saved_count = service.save_samples(
        employee,
        collector,
    )

    assert saved_count == 10

    assert (
        milvus_repository.insert_embedding.call_count
        == 10
    )

    first_call = (
        milvus_repository.insert_embedding.call_args_list[0]
    )

    arguments = first_call.kwargs

    assert arguments["employee_id"] == "EMP001"
    assert arguments["model_name"] == "w600k_r50"
    assert arguments["model_version"] == "buffalo_l"
    assert arguments["embedding_version"] == "1"
    assert len(arguments["embedding"]) == 512

def test_save_samples_rolls_back_on_milvus_failure() -> None:
    service, _, _, milvus_repository = create_service()

    collector = service.create_collector()
    employee = create_employee()

    for index in range(10):
        embedding = np.zeros(
            512,
            dtype=np.float32,
        )

        embedding[index] = 1.0
        collector.add(embedding)

    calls = 0

    def insert_side_effect(**kwargs):
        nonlocal calls
        calls += 1

        if calls == 4:
            raise RuntimeError("Milvus insert failed")

    milvus_repository.insert_embedding.side_effect = (
        insert_side_effect
    )

    with pytest.raises(
        RuntimeError,
        match="Milvus insert failed",
    ):
        service.save_samples(
            employee,
            collector,
        )

    milvus_repository.delete_vectors.assert_called_once()

    deleted_ids = (
        milvus_repository
        .delete_vectors
        .call_args.args[0]
    )

    assert len(deleted_ids) == 3

def test_reenrollment_replaces_old_embeddings() -> None:
    service, _, _, milvus_repository = create_service()

    collector = service.create_collector()
    employee = create_employee()

    for index in range(10):
        embedding = np.zeros(512, dtype=np.float32)
        embedding[index] = 1.0
        collector.add(embedding)

    milvus_repository.get_employee_embeddings.return_value = [
        {"vector_id": 1001},
        {"vector_id": 1002},
        {"vector_id": 1003},
    ]

    saved_count = service.save_samples(
        employee,
        collector,
    )

    assert saved_count == 10

    milvus_repository.delete_vectors.assert_called_once_with(
        [1001, 1002, 1003]
    )

    assert (
        milvus_repository.insert_embedding.call_count
        == 10
    )


def test_reenrollment_failure_keeps_old_embeddings() -> None:
    service, _, _, milvus_repository = create_service()

    collector = service.create_collector()
    employee = create_employee()

    for index in range(10):
        embedding = np.zeros(512, dtype=np.float32)
        embedding[index] = 1.0
        collector.add(embedding)

    milvus_repository.get_employee_embeddings.return_value = [
        {"vector_id": 1001},
        {"vector_id": 1002},
        {"vector_id": 1003},
    ]

    calls = 0

    def insert_side_effect(**kwargs):
        nonlocal calls
        calls += 1

        if calls == 4:
            raise RuntimeError("Milvus insert failed")

    milvus_repository.insert_embedding.side_effect = (
        insert_side_effect
    )

    with pytest.raises(
        RuntimeError,
        match="Milvus insert failed",
    ):
        service.save_samples(
            employee,
            collector,
        )

    # New partial vectors are cleaned up.
    cleanup_ids = (
        milvus_repository
        .delete_vectors
        .call_args.args[0]
    )

    assert len(cleanup_ids) == 3

    # Old vectors must NOT be deleted.
    assert cleanup_ids != [1001, 1002, 1003]


def _make_dummy_image_bytes() -> bytes:
    import cv2
    img = np.zeros((100, 100, 3), dtype=np.uint8)
    _, buf = cv2.imencode(".jpg", img)
    return buf.tobytes()


def test_enroll_samples_success() -> None:
    service, face_engine, quality_service, milvus_repository = create_service()
    employee = create_employee()

    # Provide 10 distinct embeddings
    embeddings = []
    for i in range(10):
        emb = Mock()
        vec = np.zeros(512, dtype=np.float32)
        vec[i] = 1.0
        emb.vector = vec
        embeddings.append(emb)

    detection = Mock()
    face_engine.process.side_effect = [
        ([detection], [embeddings[i]]) for i in range(10)
    ]
    quality_service.is_acceptable.return_value = True

    dummy_images = [_make_dummy_image_bytes() for _ in range(10)]

    saved_count = service.enroll_samples(
        employee=employee,
        image_bytes_list=dummy_images,
    )

    assert saved_count == 10
    assert milvus_repository.insert_embedding.call_count == 10


def test_enroll_samples_incorrect_count() -> None:
    service, _, _, _ = create_service()
    employee = create_employee()

    dummy_images = [_make_dummy_image_bytes() for _ in range(7)]

    with pytest.raises(
        ValueError,
        match="Exactly 10 face sample images are required",
    ):
        service.enroll_samples(
            employee=employee,
            image_bytes_list=dummy_images,
        )


def test_enroll_samples_invalid_image() -> None:
    service, face_engine, quality_service, _ = create_service()
    employee = create_employee()

    detection = Mock()
    embeddings = []
    for i in range(9):
        emb = Mock()
        vec = np.zeros(512, dtype=np.float32)
        vec[i] = 1.0
        emb.vector = vec
        embeddings.append(emb)

    face_engine.process.side_effect = [
        ([detection], [embeddings[i]]) for i in range(9)
    ]
    quality_service.is_acceptable.return_value = True

    dummy_images = [_make_dummy_image_bytes() for _ in range(9)]
    dummy_images.append(b"not_an_image")

    with pytest.raises(
        ValueError,
        match="Sample 10: Invalid or unreadable image format",
    ):
        service.enroll_samples(
            employee=employee,
            image_bytes_list=dummy_images,
        )



def test_enroll_samples_no_face_detected() -> None:
    service, face_engine, _, _ = create_service()
    employee = create_employee()

    face_engine.process.return_value = ([], [])
    dummy_images = [_make_dummy_image_bytes() for _ in range(10)]

    with pytest.raises(
        ValueError,
        match="Sample 1: No face detected",
    ):
        service.enroll_samples(
            employee=employee,
            image_bytes_list=dummy_images,
        )


def test_enroll_samples_multiple_faces_detected() -> None:
    service, face_engine, _, _ = create_service()
    employee = create_employee()

    det1, det2 = Mock(), Mock()
    emb1, emb2 = Mock(), Mock()
    face_engine.process.return_value = ([det1, det2], [emb1, emb2])
    dummy_images = [_make_dummy_image_bytes() for _ in range(10)]

    with pytest.raises(
        ValueError,
        match="Sample 1: Multiple faces detected",
    ):
        service.enroll_samples(
            employee=employee,
            image_bytes_list=dummy_images,
        )


def test_enroll_samples_quality_failed() -> None:
    service, face_engine, quality_service, _ = create_service()
    employee = create_employee()

    detection = Mock()
    embedding = Mock()
    embedding.vector = np.ones(512, dtype=np.float32)

    face_engine.process.return_value = ([detection], [embedding])
    quality_service.is_acceptable.return_value = False

    dummy_images = [_make_dummy_image_bytes() for _ in range(10)]

    with pytest.raises(
        ValueError,
        match="Sample 1: Face quality check failed",
    ):
        service.enroll_samples(
            employee=employee,
            image_bytes_list=dummy_images,
        )


def test_enroll_samples_duplicate_detected() -> None:
    service, face_engine, quality_service, _ = create_service()
    employee = create_employee()

    # Return the exact same embedding for sample 1 and sample 2
    detection = Mock()
    embedding = Mock()
    embedding.vector = np.ones(512, dtype=np.float32)

    face_engine.process.return_value = ([detection], [embedding])
    quality_service.is_acceptable.return_value = True

    dummy_images = [_make_dummy_image_bytes() for _ in range(10)]

    with pytest.raises(
        ValueError,
        match="Sample 2: Duplicate face image detected",
    ):
        service.enroll_samples(
            employee=employee,
            image_bytes_list=dummy_images,
        )


def test_enroll_samples_milvus_rollback() -> None:
    service, face_engine, quality_service, milvus_repository = create_service()
    employee = create_employee()

    embeddings = []
    for i in range(10):
        emb = Mock()
        vec = np.zeros(512, dtype=np.float32)
        vec[i] = 1.0
        emb.vector = vec
        embeddings.append(emb)

    detection = Mock()
    face_engine.process.side_effect = [
        ([detection], [embeddings[i]]) for i in range(10)
    ]
    quality_service.is_acceptable.return_value = True

    calls = 0

    def insert_side_effect(**kwargs):
        nonlocal calls
        calls += 1
        if calls == 6:
            raise RuntimeError("Milvus connection dropped")

    milvus_repository.insert_embedding.side_effect = insert_side_effect

    dummy_images = [_make_dummy_image_bytes() for _ in range(10)]

    with pytest.raises(
        RuntimeError,
        match="Milvus connection dropped",
    ):
        service.enroll_samples(
            employee=employee,
            image_bytes_list=dummy_images,
        )

    milvus_repository.delete_vectors.assert_called_once()
    deleted_ids = milvus_repository.delete_vectors.call_args.args[0]
    assert len(deleted_ids) == 5