import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RecognitionConfirmation:
    employee_id: str
    confirmed: bool


class RecognitionStabilityService:
    def __init__(
        self,
        required_matches: int = 5,
    ) -> None:
        if required_matches < 1:
            raise ValueError(
                "required_matches must be at least 1"
            )

        self._required_matches = required_matches
        self._last_employee_id: str | None = None
        self._consecutive_matches = 0
        self._confirmed_employee_ids: set[str] = set()

    def process(
        self,
        employee_id: str | None,
    ) -> RecognitionConfirmation | None:
        if employee_id is None:
            logger.debug(
                "Unknown face detected. Resetting recognition stability."
            )
            self.reset()
            return None

        if employee_id in self._confirmed_employee_ids:
            logger.debug(
                "Employee already confirmed in current recognition cycle | employee_id=%s",
                employee_id,
            )
            return RecognitionConfirmation(
                employee_id=employee_id,
                confirmed=False,
            )

        if employee_id == self._last_employee_id:
            self._consecutive_matches += 1
            logger.debug(
                "Recognition streak incremented | employee_id=%s | matches=%s/%s",
                employee_id,
                self._consecutive_matches,
                self._required_matches,
            )
        else:
            logger.debug(
                "Recognition streak started/reset | employee_id=%s",
                employee_id,
            )
            self._last_employee_id = employee_id
            self._consecutive_matches = 1

        if (
            self._consecutive_matches
            < self._required_matches
        ):
            return RecognitionConfirmation(
                employee_id=employee_id,
                confirmed=False,
            )

        logger.info(
            "Recognition confirmed | employee_id=%s | matches=%s",
            employee_id,
            self._consecutive_matches,
        )

        self._confirmed_employee_ids.add(employee_id)
        self._reset_current_streak()

        return RecognitionConfirmation(
            employee_id=employee_id,
            confirmed=True,
        )

    def reset(self) -> None:
        logger.debug("Recognition stability fully reset")
        self._last_employee_id = None
        self._consecutive_matches = 0
        self._confirmed_employee_ids.clear()

    def _reset_current_streak(self) -> None:
        self._last_employee_id = None
        self._consecutive_matches = 0