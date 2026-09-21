from datetime import datetime, timedelta

from app.services.recognition_cooldown import (
    RecognitionCooldown,
)


def test_first_recognition_can_be_processed() -> None:
    cooldown = RecognitionCooldown(
        cooldown_seconds=5,
    )

    now = datetime(
        2026,
        8,
        23,
        9,
        0,
        0,
    )

    result = cooldown.can_process(
        "EMP001",
        now=now,
    )

    assert result is True


def test_recognition_is_blocked_within_cooldown() -> None:
    cooldown = RecognitionCooldown(
        cooldown_seconds=5,
    )

    now = datetime(
        2026,
        8,
        23,
        9,
        0,
        0,
    )

    cooldown.mark_processed(
        "EMP001",
        now=now,
    )

    result = cooldown.can_process(
        "EMP001",
        now=now + timedelta(seconds=3),
    )

    assert result is False


def test_recognition_can_be_processed_after_cooldown() -> None:
    cooldown = RecognitionCooldown(
        cooldown_seconds=5,
    )

    now = datetime(
        2026,
        8,
        23,
        9,
        0,
        0,
    )

    cooldown.mark_processed(
        "EMP001",
        now=now,
    )

    result = cooldown.can_process(
        "EMP001",
        now=now + timedelta(seconds=5),
    )

    assert result is True


def test_cooldown_is_separate_for_each_employee() -> None:
    cooldown = RecognitionCooldown(
        cooldown_seconds=5,
    )

    now = datetime(
        2026,
        8,
        23,
        9,
        0,
        0,
    )

    cooldown.mark_processed(
        "EMP001",
        now=now,
    )

    result = cooldown.can_process(
        "EMP002",
        now=now + timedelta(seconds=1),
    )

    assert result is True