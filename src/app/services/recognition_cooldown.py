import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class RecognitionCooldown:
    def __init__(
        self,
        cooldown_seconds: int = 5,
    ) -> None:
        self._cooldown = timedelta(
            seconds=cooldown_seconds,
        )

        self._last_processed: dict[str, datetime] = {}

    def can_process(
        self,
        employee_id: str,
        *,
        now: datetime | None = None,
    ) -> bool:
        current_time = now or datetime.now()

        last_processed = self._last_processed.get(
            employee_id,
        )

        if last_processed is None:
            logger.debug(
                "Recognition cooldown allowed | employee_id=%s | reason=first_processing",
                employee_id,
            )
            return True

        elapsed = current_time - last_processed
        allowed = elapsed >= self._cooldown

        logger.debug(
            "Recognition cooldown checked | employee_id=%s | allowed=%s",
            employee_id,
            allowed,
        )

        return allowed

    def mark_processed(
        self,
        employee_id: str,
        *,
        now: datetime | None = None,
    ) -> None:
        current_time = now or datetime.now()

        self._last_processed[employee_id] = current_time

        logger.debug(
            "Recognition marked as processed | employee_id=%s",
            employee_id,
        )