import logging

from app.application.face_scanner_application import (
    FaceScannerApplication,
)
from app.core.logging_config import configure_logging
from app.models.scanner_type import ScannerType


logger = logging.getLogger(__name__)


def main() -> None:
    configure_logging()

    logger.info("======================================")
    logger.info("CHECK-IN FACE SCANNER STARTED")
    logger.info("Press Q to exit")
    logger.info("======================================")

    application = FaceScannerApplication(
        scanner_type=ScannerType.CHECK_IN,
    )

    application.run()


if __name__ == "__main__":
    main()