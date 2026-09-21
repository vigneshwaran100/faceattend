import pytest

from app.services.recognition_stability_service import (
    RecognitionStabilityService,
)


def test_confirms_after_required_consecutive_matches() -> None:
    service = RecognitionStabilityService(
        required_matches=3,
    )

    first = service.process("EMP001")
    second = service.process("EMP001")
    third = service.process("EMP001")

    assert first is not None
    assert first.confirmed is False

    assert second is not None
    assert second.confirmed is False

    assert third is not None
    assert third.confirmed is True
    assert third.employee_id == "EMP001"


def test_different_employee_resets_streak() -> None:
    service = RecognitionStabilityService(
        required_matches=3,
    )

    service.process("EMP001")
    service.process("EMP001")

    result = service.process("EMP002")

    assert result is not None
    assert result.confirmed is False

    result = service.process("EMP002")
    assert result is not None
    assert result.confirmed is False

    result = service.process("EMP002")
    assert result is not None
    assert result.confirmed is True
    assert result.employee_id == "EMP002"


def test_unknown_face_resets_streak() -> None:
    service = RecognitionStabilityService(
        required_matches=3,
    )

    service.process("EMP001")
    service.process("EMP001")

    result = service.process(None)

    assert result is None

    result = service.process("EMP001")
    assert result is not None
    assert result.confirmed is False

    result = service.process("EMP001")
    assert result is not None
    assert result.confirmed is False

    result = service.process("EMP001")
    assert result is not None
    assert result.confirmed is True


def test_confirmed_employee_is_not_confirmed_again() -> None:
    service = RecognitionStabilityService(
        required_matches=2,
    )

    service.process("EMP001")

    result = service.process("EMP001")

    assert result is not None
    assert result.confirmed is True

    result = service.process("EMP001")

    assert result is not None
    assert result.confirmed is False
    assert result.employee_id == "EMP001"


def test_reset_allows_employee_to_be_confirmed_again() -> None:
    service = RecognitionStabilityService(
        required_matches=2,
    )

    service.process("EMP001")
    result = service.process("EMP001")

    assert result is not None
    assert result.confirmed is True

    service.reset()

    result = service.process("EMP001")

    assert result is not None
    assert result.confirmed is False

    result = service.process("EMP001")

    assert result is not None
    assert result.confirmed is True

def test_unknown_face_after_confirmation_resets_stability():
    service = RecognitionStabilityService(required_matches=2)

    first = service.process("EMP001")
    assert first.confirmed is False

    confirmed = service.process("EMP001")
    assert confirmed.confirmed is True

    # Employee leaves the camera
    service.process(None)

    # Same employee can now start a new recognition cycle
    first_again = service.process("EMP001")
    assert first_again.confirmed is False

    confirmed_again = service.process("EMP001")
    assert confirmed_again.confirmed is True

def test_rejects_invalid_required_matches() -> None:
    with pytest.raises(
        ValueError,
        match="required_matches must be at least 1",
    ):
        RecognitionStabilityService(
            required_matches=0,
        )
        