from datetime import datetime, timezone
import io
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import (
    get_current_user,
    get_employee_repository,
    get_face_enrollment_service,
)
from app.api.main import app
from app.models.employee import Employee
from app.models.user import User


def create_test_employee(
    employee_id: str = "EMP001",
    status: str = "active",
) -> Employee:
    now = datetime.now(timezone.utc)
    return Employee(
        employee_id=employee_id,
        name="Test Employee",
        email="test@example.com",
        team_id="TEAM001",
        department_id="DEPT001",
        designation="Engineer",
        status=status,
        created_at=now,
        updated_at=now,
    )


@pytest.fixture
def employee_repository() -> Mock:
    return Mock()


@pytest.fixture
def enrollment_service() -> Mock:
    return Mock()


@pytest.fixture
def client(
    employee_repository: Mock,
    enrollment_service: Mock,
) -> TestClient:
    now = datetime.now(timezone.utc)
    admin_user = User(
        id="ADMIN01",
        username="admin",
        password_hash="hash",
        role="admin",
        status="active",
        created_at=now,
        updated_at=now,
    )
    app.dependency_overrides[get_current_user] = lambda: admin_user
    app.dependency_overrides[get_employee_repository] = (
        lambda: employee_repository
    )
    app.dependency_overrides[get_face_enrollment_service] = (
        lambda: enrollment_service
    )

    test_client = TestClient(app, raise_server_exceptions=False)
    yield test_client
    app.dependency_overrides.clear()


def _create_files_payload(count: int = 10, filename_prefix: str = "sample") -> list[tuple]:
    files = []
    for i in range(count):
        file_content = io.BytesIO(b"\xff\xd8\xff\xe0\x00\x10JFIF\x00dummy_jpg_bytes")
        files.append(
            ("images", (f"{filename_prefix}_{i}.jpg", file_content, "image/jpeg"))
        )
    return files


def test_enroll_face_samples_success(
    client: TestClient,
    employee_repository: Mock,
    enrollment_service: Mock,
) -> None:
    employee = create_test_employee("EMP001", "active")
    employee_repository.get_by_id.return_value = employee
    enrollment_service.enroll_samples.return_value = 10

    files = _create_files_payload(10)
    response = client.post("/employees/EMP001/face/samples", files=files)

    assert response.status_code == 201
    data = response.json()
    assert data["employee_id"] == "EMP001"
    assert data["samples_received"] == 10
    assert data["embeddings_stored"] == 10
    assert data["enrollment_status"] == "success"
    assert "Successfully enrolled 10 face samples" in data["message"]

    enrollment_service.enroll_samples.assert_called_once()
    call_kwargs = enrollment_service.enroll_samples.call_args.kwargs
    assert call_kwargs["employee"] == employee
    assert len(call_kwargs["image_bytes_list"]) == 10


def test_enroll_face_samples_employee_not_found(
    client: TestClient,
    employee_repository: Mock,
    enrollment_service: Mock,
) -> None:
    employee_repository.get_by_id.return_value = None

    files = _create_files_payload(10)
    response = client.post("/employees/UNKNOWN/face/samples", files=files)

    assert response.status_code == 404
    data = response.json()
    assert "employee not found" in data["detail"].lower()
    enrollment_service.enroll_samples.assert_not_called()


def test_enroll_face_samples_employee_inactive(
    client: TestClient,
    employee_repository: Mock,
    enrollment_service: Mock,
) -> None:
    employee = create_test_employee("EMP002", "inactive")
    employee_repository.get_by_id.return_value = employee

    files = _create_files_payload(10)
    response = client.post("/employees/EMP002/face/samples", files=files)

    assert response.status_code == 400
    data = response.json()
    assert "not active" in data["detail"].lower()
    enrollment_service.enroll_samples.assert_not_called()


def test_enroll_face_samples_incorrect_sample_count_less(
    client: TestClient,
    employee_repository: Mock,
    enrollment_service: Mock,
) -> None:
    employee = create_test_employee("EMP001", "active")
    employee_repository.get_by_id.return_value = employee

    files = _create_files_payload(7)
    response = client.post("/employees/EMP001/face/samples", files=files)

    assert response.status_code == 400
    data = response.json()
    assert "exactly 10 face sample images are required" in data["detail"].lower()
    enrollment_service.enroll_samples.assert_not_called()


def test_enroll_face_samples_incorrect_sample_count_more(
    client: TestClient,
    employee_repository: Mock,
    enrollment_service: Mock,
) -> None:
    employee = create_test_employee("EMP001", "active")
    employee_repository.get_by_id.return_value = employee

    files = _create_files_payload(12)
    response = client.post("/employees/EMP001/face/samples", files=files)

    assert response.status_code == 400
    data = response.json()
    assert "exactly 10 face sample images are required" in data["detail"].lower()
    enrollment_service.enroll_samples.assert_not_called()


def test_enroll_face_samples_invalid_file_type(
    client: TestClient,
    employee_repository: Mock,
    enrollment_service: Mock,
) -> None:
    employee = create_test_employee("EMP001", "active")
    employee_repository.get_by_id.return_value = employee

    files = [
        ("images", ("sample_0.pdf", io.BytesIO(b"%PDF-1.4 dummy"), "application/pdf")),
    ] + _create_files_payload(9)

    response = client.post("/employees/EMP001/face/samples", files=files)

    assert response.status_code == 400
    data = response.json()
    assert "must be an image" in data["detail"].lower()
    enrollment_service.enroll_samples.assert_not_called()


def test_enroll_face_samples_empty_image(
    client: TestClient,
    employee_repository: Mock,
    enrollment_service: Mock,
) -> None:
    employee = create_test_employee("EMP001", "active")
    employee_repository.get_by_id.return_value = employee

    files = [
        ("images", ("sample_0.jpg", io.BytesIO(b""), "image/jpeg")),
    ] + _create_files_payload(9)

    response = client.post("/employees/EMP001/face/samples", files=files)

    assert response.status_code == 400
    data = response.json()
    assert "empty" in data["detail"].lower()
    enrollment_service.enroll_samples.assert_not_called()


def test_enroll_face_samples_duplicate_sample_error(
    client: TestClient,
    employee_repository: Mock,
    enrollment_service: Mock,
) -> None:
    employee = create_test_employee("EMP001", "active")
    employee_repository.get_by_id.return_value = employee
    enrollment_service.enroll_samples.side_effect = ValueError(
        "Sample 2: Duplicate face image detected. Each of the 10 samples must be a distinct pose or capture"
    )

    files = _create_files_payload(10)
    response = client.post("/employees/EMP001/face/samples", files=files)

    assert response.status_code == 400
    data = response.json()
    assert "duplicate face image detected" in data["detail"].lower()


def test_enroll_face_samples_internal_error_and_rollback(
    client: TestClient,
    employee_repository: Mock,
    enrollment_service: Mock,
) -> None:
    employee = create_test_employee("EMP001", "active")
    employee_repository.get_by_id.return_value = employee
    enrollment_service.enroll_samples.side_effect = RuntimeError(
        "Milvus storage failed"
    )

    files = _create_files_payload(10)
    response = client.post("/employees/EMP001/face/samples", files=files)

    assert response.status_code == 500
    data = response.json()
    assert "internal server error" in data["detail"].lower()
