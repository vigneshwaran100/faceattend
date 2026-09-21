import logging

from app.application.face_scanner_application import (
    FaceScannerApplication,
)
from app.core.config import settings
from app.core.logging import configure_logging


def main() -> None:
    configure_logging()

    logger = logging.getLogger(__name__)

    logger.info("Face Recognition System started")

    scanner = FaceScannerApplication(
        scanner_type=settings.scanner_mode,
    )

    scanner.run()


if __name__ == "__main__":
    main()