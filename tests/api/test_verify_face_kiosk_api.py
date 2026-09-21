from datetime import date, datetime, time
from unittest.mock import MagicMock, Mock
import io
import cv2
import numpy as np
import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import (
    get_attendance_service,
    get_current_user,
    get_employee_repository,
    get_face_engine,
    get_face_recognition_service,
    get_scanner_audit_service,
    require_authenticated,
)
from app.api.main import app
from app.models.attendance import Attendance
from app.models.employee import Employee
from app.models.face import FaceDetection, FaceEmbedding
from app.models.user import User
from app.services.face_recognition_service import RecognitionResult


@pytest.fixture
def mock_user() -> User:
    return User(
        id="user-1",
        username="kiosk_operator",
        password_hash="hashed",
        role="admin",
        status="active",
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )


@pytest.fixture
def sample_image_bytes() -> bytes:
    img = np.zeros((200, 200, 3), dtype=np.uint8)
    _, encoded = cv2.imencode(".jpg", img)
    return encoded.tobytes()


@pytest.fixture
def sample_detection() -> FaceDetection:
    return FaceDetection(
        bounding_box=(20, 20, 150, 150),
        confidence=0.95,
        landmarks=None,
    )


@pytest.fixture
def sample_embedding() -> FaceEmbedding:
    return FaceEmbedding(
        vector=np.array([0.1] * 512, dtype=np.float32),
    )


@pytest.fixture
def sample_active_employee() -> Employee:
    return Employee(
        employee_id="EMP001",
        name="John Doe",
        email="john@example.com",
        team_id="team-1",
        department_id="Engineering",
        designation="Software Engineer",
        status="active",
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )


@pytest.fixture
def sample_inactive_employee() -> Employee:
    return Employee(
        employee_id="EMP002",
        name="Jane Inactive",
        email="jane@example.com",
        team_id="team-1",
        department_id="HR",
        designation="HR Executive",
        status="inactive",
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )


def test_verify_face_no_face_detected(
    mock_user: User, sample_image_bytes: bytes
) -> None:
    mock_face_engine = Mock()
    mock_face_engine.process.return_value = ([], [])
    mock_audit = Mock()

    app.dependency_overrides[require_authenticated] = lambda: mock_user
    app.dependency_overrides[get_face_engine] = lambda: mock_face_engine
    app.dependency_overrides[get_scanner_audit_service] = lambda: mock_audit

    try:
        client = TestClient(app)
        response = client.post(
            "/attendance/verify-face",
            data={"scanner_type": "CHECK_IN"},
            files={"image": ("frame.jpg", sample_image_bytes, "image/jpeg")},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert data["status"] == "NO_FACE_DETECTED"
        mock_audit.log_event.assert_called_once()
        assert mock_audit.log_event.call_args.kwargs["event_type"] == "no_face_detected"
        assert mock_audit.log_event.call_args.kwargs["status"] == "FAILURE"
    finally:
        app.dependency_overrides.clear()


def test_verify_face_multiple_faces_detected(
    mock_user: User,
    sample_image_bytes: bytes,
    sample_detection: FaceDetection,
    sample_embedding: FaceEmbedding,
) -> None:
    mock_face_engine = Mock()
    det2 = FaceDetection(bounding_box=(50, 50, 120, 120), confidence=0.88, landmarks=None)
    emb2 = FaceEmbedding(vector=np.array([0.2] * 512, dtype=np.float32))
    mock_face_engine.process.return_value = (
        [sample_detection, det2],
        [sample_embedding, emb2],
    )
    mock_audit = Mock()

    app.dependency_overrides[require_authenticated] = lambda: mock_user
    app.dependency_overrides[get_face_engine] = lambda: mock_face_engine
    app.dependency_overrides[get_scanner_audit_service] = lambda: mock_audit

    try:
        client = TestClient(app)
        response = client.post(
            "/attendance/verify-face",
            data={"scanner_type": "CHECK_IN"},
            files={"image": ("frame.jpg", sample_image_bytes, "image/jpeg")},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert data["status"] == "MULTIPLE_FACES_DETECTED"
        assert "Multiple faces detected (2)" in data["message"]
        mock_audit.log_event.assert_called_once()
        assert mock_audit.log_event.call_args.kwargs["event_type"] == "multiple_faces"
        assert mock_audit.log_event.call_args.kwargs["status"] == "FAILURE"
    finally:
        app.dependency_overrides.clear()


def test_verify_face_unrecognized_face(
    mock_user: User,
    sample_image_bytes: bytes,
    sample_detection: FaceDetection,
    sample_embedding: FaceEmbedding,
) -> None:
    mock_face_engine = Mock()
    mock_face_engine.process.return_value = ([sample_detection], [sample_embedding])
    mock_rec = Mock()
    mock_rec.recognize.return_value = RecognitionResult(
        recognized=False,
        employee_id=None,
        similarity=0.45,
    )
    mock_audit = Mock()

    app.dependency_overrides[require_authenticated] = lambda: mock_user
    app.dependency_overrides[get_face_engine] = lambda: mock_face_engine
    app.dependency_overrides[get_face_recognition_service] = lambda: mock_rec
    app.dependency_overrides[get_scanner_audit_service] = lambda: mock_audit

    try:
        client = TestClient(app)
        response = client.post(
            "/attendance/verify-face",
            data={"scanner_type": "CHECK_IN"},
            files={"image": ("frame.jpg", sample_image_bytes, "image/jpeg")},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert data["status"] == "UNRECOGNIZED_FACE"
        assert data["similarity"] == 0.45
        mock_audit.log_event.assert_called_once()
        assert mock_audit.log_event.call_args.kwargs["event_type"] == "recognition_failed"
        assert mock_audit.log_event.call_args.kwargs["status"] == "FAILURE"
    finally:
        app.dependency_overrides.clear()


def test_verify_face_employee_not_found_in_db(
    mock_user: User,
    sample_image_bytes: bytes,
    sample_detection: FaceDetection,
    sample_embedding: FaceEmbedding,
) -> None:
    mock_face_engine = Mock()
    mock_face_engine.process.return_value = ([sample_detection], [sample_embedding])
    mock_rec = Mock()
    mock_rec.recognize.return_value = RecognitionResult(
        recognized=True,
        employee_id="GHOST_EMP_999",
        similarity=0.88,
    )
    mock_emp_repo = Mock()
    mock_emp_repo.get_by_id.return_value = None
    mock_audit = Mock()

    app.dependency_overrides[require_authenticated] = lambda: mock_user
    app.dependency_overrides[get_face_engine] = lambda: mock_face_engine
    app.dependency_overrides[get_face_recognition_service] = lambda: mock_rec
    app.dependency_overrides[get_employee_repository] = lambda: mock_emp_repo
    app.dependency_overrides[get_scanner_audit_service] = lambda: mock_audit

    try:
        client = TestClient(app)
        response = client.post(
            "/attendance/verify-face",
            data={"scanner_type": "CHECK_IN"},
            files={"image": ("frame.jpg", sample_image_bytes, "image/jpeg")},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert data["status"] == "EMPLOYEE_NOT_FOUND"
        assert data["employee_id"] == "GHOST_EMP_999"
        mock_audit.log_event.assert_called_once()
        assert mock_audit.log_event.call_args.kwargs["event_type"] == "employee_not_found"
        assert mock_audit.log_event.call_args.kwargs["status"] == "FAILURE"
    finally:
        app.dependency_overrides.clear()


def test_verify_face_inactive_employee(
    mock_user: User,
    sample_image_bytes: bytes,
    sample_detection: FaceDetection,
    sample_embedding: FaceEmbedding,
    sample_inactive_employee: Employee,
) -> None:
    mock_face_engine = Mock()
    mock_face_engine.process.return_value = ([sample_detection], [sample_embedding])
    mock_rec = Mock()
    mock_rec.recognize.return_value = RecognitionResult(
        recognized=True,
        employee_id=sample_inactive_employee.employee_id,
        similarity=0.91,
    )
    mock_emp_repo = Mock()
    mock_emp_repo.get_by_id.return_value = sample_inactive_employee
    mock_audit = Mock()

    app.dependency_overrides[require_authenticated] = lambda: mock_user
    app.dependency_overrides[get_face_engine] = lambda: mock_face_engine
    app.dependency_overrides[get_face_recognition_service] = lambda: mock_rec
    app.dependency_overrides[get_employee_repository] = lambda: mock_emp_repo
    app.dependency_overrides[get_scanner_audit_service] = lambda: mock_audit

    try:
        client = TestClient(app)
        response = client.post(
            "/attendance/verify-face",
            data={"scanner_type": "CHECK_IN"},
            files={"image": ("frame.jpg", sample_image_bytes, "image/jpeg")},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert data["status"] == "INACTIVE_EMPLOYEE"
        assert data["employee_id"] == sample_inactive_employee.employee_id
        mock_audit.log_event.assert_called_once()
        assert mock_audit.log_event.call_args.kwargs["event_type"] == "inactive_employee"
        assert mock_audit.log_event.call_args.kwargs["status"] == "FAILURE"
    finally:
        app.dependency_overrides.clear()


def test_verify_face_check_in_success(
    mock_user: User,
    sample_image_bytes: bytes,
    sample_detection: FaceDetection,
    sample_embedding: FaceEmbedding,
    sample_active_employee: Employee,
) -> None:
    now_dt = datetime.now()
    mock_face_engine = Mock()
    mock_face_engine.process.return_value = ([sample_detection], [sample_embedding])
    mock_rec = Mock()
    mock_rec.recognize.return_value = RecognitionResult(
        recognized=True,
        employee_id=sample_active_employee.employee_id,
        similarity=0.93,
    )
    mock_emp_repo = Mock()
    mock_emp_repo.get_by_id.return_value = sample_active_employee
    mock_att = Mock()
    mock_att.check_in.return_value = Attendance(
        attendance_id="att-101",
        employee_id=sample_active_employee.employee_id,
        attendance_date=date.today(),
        check_in=time(9, 0),
        check_out=None,
        status="in_progress",
        created_at=now_dt,
        updated_at=now_dt,
    )
    mock_audit = Mock()

    app.dependency_overrides[require_authenticated] = lambda: mock_user
    app.dependency_overrides[get_face_engine] = lambda: mock_face_engine
    app.dependency_overrides[get_face_recognition_service] = lambda: mock_rec
    app.dependency_overrides[get_employee_repository] = lambda: mock_emp_repo
    app.dependency_overrides[get_attendance_service] = lambda: mock_att
    app.dependency_overrides[get_scanner_audit_service] = lambda: mock_audit

    try:
        client = TestClient(app)
        response = client.post(
            "/attendance/verify-face",
            data={"scanner_type": "CHECK_IN"},
            files={"image": ("frame.jpg", sample_image_bytes, "image/jpeg")},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["status"] == "ACCESS_GRANTED"
        assert data["employee_id"] == sample_active_employee.employee_id
        assert data["employee_name"] == sample_active_employee.name
        assert data["attendance_id"] == "att-101"
        mock_audit.log_event.assert_called_once()
        assert mock_audit.log_event.call_args.kwargs["event_type"] == "face_scan"
        assert mock_audit.log_event.call_args.kwargs["status"] == "SUCCESS"
    finally:
        app.dependency_overrides.clear()


def test_verify_face_check_out_success(
    mock_user: User,
    sample_image_bytes: bytes,
    sample_detection: FaceDetection,
    sample_embedding: FaceEmbedding,
    sample_active_employee: Employee,
) -> None:
    now_dt = datetime.now()
    mock_face_engine = Mock()
    mock_face_engine.process.return_value = ([sample_detection], [sample_embedding])
    mock_rec = Mock()
    mock_rec.recognize.return_value = RecognitionResult(
        recognized=True,
        employee_id=sample_active_employee.employee_id,
        similarity=0.92,
    )
    mock_emp_repo = Mock()
    mock_emp_repo.get_by_id.return_value = sample_active_employee
    mock_att = Mock()
    mock_att.check_out.return_value = Attendance(
        attendance_id="att-101",
        employee_id=sample_active_employee.employee_id,
        attendance_date=date.today(),
        check_in=time(9, 0),
        check_out=time(18, 0),
        status="present",
        created_at=now_dt,
        updated_at=now_dt,
    )
    mock_audit = Mock()

    app.dependency_overrides[require_authenticated] = lambda: mock_user
    app.dependency_overrides[get_face_engine] = lambda: mock_face_engine
    app.dependency_overrides[get_face_recognition_service] = lambda: mock_rec
    app.dependency_overrides[get_employee_repository] = lambda: mock_emp_repo
    app.dependency_overrides[get_attendance_service] = lambda: mock_att
    app.dependency_overrides[get_scanner_audit_service] = lambda: mock_audit

    try:
        client = TestClient(app)
        response = client.post(
            "/attendance/verify-face",
            data={"scanner_type": "CHECK_OUT"},
            files={"image": ("frame.jpg", sample_image_bytes, "image/jpeg")},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["status"] == "ACCESS_GRANTED"
        assert data["employee_id"] == sample_active_employee.employee_id
        assert data["attendance_id"] == "att-101"
        mock_audit.log_event.assert_called_once()
        assert mock_audit.log_event.call_args.kwargs["event_type"] == "face_scan"
        assert mock_audit.log_event.call_args.kwargs["status"] == "SUCCESS"
    finally:
        app.dependency_overrides.clear()


def test_verify_face_check_out_no_check_in_error(
    mock_user: User,
    sample_image_bytes: bytes,
    sample_detection: FaceDetection,
    sample_embedding: FaceEmbedding,
    sample_active_employee: Employee,
) -> None:
    mock_face_engine = Mock()
    mock_face_engine.process.return_value = ([sample_detection], [sample_embedding])
    mock_rec = Mock()
    mock_rec.recognize.return_value = RecognitionResult(
        recognized=True,
        employee_id=sample_active_employee.employee_id,
        similarity=0.94,
    )
    mock_emp_repo = Mock()
    mock_emp_repo.get_by_id.return_value = sample_active_employee
    mock_att = Mock()
    mock_att.check_out.side_effect = ValueError(f"No attendance record found for {sample_active_employee.employee_id}")
    mock_audit = Mock()

    app.dependency_overrides[require_authenticated] = lambda: mock_user
    app.dependency_overrides[get_face_engine] = lambda: mock_face_engine
    app.dependency_overrides[get_face_recognition_service] = lambda: mock_rec
    app.dependency_overrides[get_employee_repository] = lambda: mock_emp_repo
    app.dependency_overrides[get_attendance_service] = lambda: mock_att
    app.dependency_overrides[get_scanner_audit_service] = lambda: mock_audit

    try:
        client = TestClient(app)
        response = client.post(
            "/attendance/verify-face",
            data={"scanner_type": "CHECK_OUT"},
            files={"image": ("frame.jpg", sample_image_bytes, "image/jpeg")},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert data["status"] == "NO_CHECK_IN"
        assert data["attendance_id"] is None
        assert "No check-in record found" in data["message"]
        mock_audit.log_event.assert_called_once()
        assert mock_audit.log_event.call_args.kwargs["event_type"] == "no_check_in"
        assert mock_audit.log_event.call_args.kwargs["status"] == "FAILURE"
    finally:
        app.dependency_overrides.clear()
