from datetime import datetime
from unittest.mock import Mock

import pytest

from app.models.employee import Employee
from app.models.scanner_type import ScannerType
from app.services.recognition_stability_service import (
    RecognitionConfirmation,
)
from app.services.scanner_orchestration_service import (
    ScannerOrchestrationService,
)


@pytest.fixture
def attendance_service():
    return Mock()


@pytest.fixture
def recognition_stability_service():
    return Mock()


@pytest.fixture
def recognition_cooldown():
    return Mock()


@pytest.fixture
def employee_repository():
    return Mock()


@pytest.fixture
def active_employee():
    return Employee(
        employee_id="EMP001",
        name="Vigneshwaran",
        email="vignesh@example.com",
        team_id="TEAM001",
        department_id="DEPT001",
        designation="AI Engineer",
        status="active",
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )


@pytest.fixture
def service(
    attendance_service,
    recognition_stability_service,
    recognition_cooldown,
    employee_repository,
):
    return ScannerOrchestrationService(
        attendance_service=attendance_service,
        recognition_stability_service=recognition_stability_service,
        recognition_cooldown=recognition_cooldown,
        employee_repository=employee_repository,
    )


def test_unknown_face_returns_failure(
    service,
    attendance_service,
    recognition_stability_service,
):
    recognition_stability_service.process.return_value = None

    result = service.process(
        employee_id=None,
        scanner_type=ScannerType.CHECK_IN,
    )

    assert result.success is False

    attendance_service.check_in.assert_not_called()
    attendance_service.check_out.assert_not_called()


def test_unstable_recognition_does_not_process_attendance(
    service,
    attendance_service,
    recognition_stability_service,
):
    recognition_stability_service.process.return_value = (
        RecognitionConfirmation(
            employee_id="EMP001",
            confirmed=False,
        )
    )

    result = service.process(
        employee_id="EMP001",
        scanner_type=ScannerType.CHECK_IN,
    )

    assert result.success is False

    attendance_service.check_in.assert_not_called()
    attendance_service.check_out.assert_not_called()


def test_unknown_employee_returns_failure(
    service,
    attendance_service,
    recognition_stability_service,
    employee_repository,
):
    recognition_stability_service.process.return_value = (
        RecognitionConfirmation(
            employee_id="EMP001",
            confirmed=True,
        )
    )

    employee_repository.get_by_id.return_value = None

    result = service.process(
        employee_id="EMP001",
        scanner_type=ScannerType.CHECK_IN,
    )

    assert result.success is False
    assert result.message == "Employee not found"

    attendance_service.check_in.assert_not_called()
    attendance_service.check_out.assert_not_called()


def test_inactive_employee_returns_failure(
    service,
    attendance_service,
    recognition_stability_service,
    employee_repository,
    active_employee,
):
    recognition_stability_service.process.return_value = (
        RecognitionConfirmation(
            employee_id="EMP001",
            confirmed=True,
        )
    )

    inactive_employee = Employee(
        employee_id="EMP001",
        name="Vigneshwaran",
        email="vignesh@example.com",
        team_id="TEAM001",
        department_id="DEPT001",
        designation="AI Engineer",
        status="inactive",
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )

    employee_repository.get_by_id.return_value = inactive_employee

    result = service.process(
        employee_id="EMP001",
        scanner_type=ScannerType.CHECK_IN,
    )

    assert result.success is False
    assert result.message == "Employee is inactive"

    attendance_service.check_in.assert_not_called()
    attendance_service.check_out.assert_not_called()


def test_cooldown_active_does_not_process_attendance(
    service,
    attendance_service,
    recognition_stability_service,
    recognition_cooldown,
    employee_repository,
    active_employee,
):
    recognition_stability_service.process.return_value = (
        RecognitionConfirmation(
            employee_id="EMP001",
            confirmed=True,
        )
    )

    employee_repository.get_by_id.return_value = active_employee
    recognition_cooldown.can_process.return_value = False

    result = service.process(
        employee_id="EMP001",
        scanner_type=ScannerType.CHECK_IN,
    )

    assert result.success is False

    attendance_service.check_in.assert_not_called()
    attendance_service.check_out.assert_not_called()

    recognition_cooldown.mark_processed.assert_not_called()


def test_confirmed_employee_checks_in(
    service,
    attendance_service,
    recognition_stability_service,
    recognition_cooldown,
    employee_repository,
    active_employee,
):
    recognition_stability_service.process.return_value = (
        RecognitionConfirmation(
            employee_id="EMP001",
            confirmed=True,
        )
    )

    employee_repository.get_by_id.return_value = active_employee
    recognition_cooldown.can_process.return_value = True

    result = service.process(
        employee_id="EMP001",
        scanner_type=ScannerType.CHECK_IN,
    )

    assert result.success is True

    attendance_service.check_in.assert_called_once_with(
        "EMP001"
    )
    attendance_service.check_out.assert_not_called()

    recognition_cooldown.mark_processed.assert_called_once_with(
        "EMP001"
    )


def test_confirmed_employee_checks_out(
    service,
    attendance_service,
    recognition_stability_service,
    recognition_cooldown,
    employee_repository,
    active_employee,
):
    recognition_stability_service.process.return_value = (
        RecognitionConfirmation(
            employee_id="EMP001",
            confirmed=True,
        )
    )

    employee_repository.get_by_id.return_value = active_employee
    recognition_cooldown.can_process.return_value = True

    result = service.process(
        employee_id="EMP001",
        scanner_type=ScannerType.CHECK_OUT,
    )

    assert result.success is True

    attendance_service.check_out.assert_called_once_with(
        "EMP001"
    )
    attendance_service.check_in.assert_not_called()

    recognition_cooldown.mark_processed.assert_called_once_with(
        "EMP001"
    )


def test_attendance_error_returns_failure(
    service,
    attendance_service,
    recognition_stability_service,
    recognition_cooldown,
    employee_repository,
    active_employee,
):
    recognition_stability_service.process.return_value = (
        RecognitionConfirmation(
            employee_id="EMP001",
            confirmed=True,
        )
    )

    employee_repository.get_by_id.return_value = active_employee
    recognition_cooldown.can_process.return_value = True

    attendance_service.check_in.side_effect = ValueError(
        "Attendance error"
    )

    result = service.process(
        employee_id="EMP001",
        scanner_type=ScannerType.CHECK_IN,
    )

    assert result.success is False

    recognition_cooldown.mark_processed.assert_not_called()