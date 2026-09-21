import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path


LOG_DIRECTORY = Path("logs")
LOG_FILE = LOG_DIRECTORY / "face_recognition.log"


def configure_logging(level: str | None = None) -> None:
    if level is None:
        try:
            from app.core.config import settings

            level = settings.log_level
        except Exception:
            level = "INFO"

    numeric_level = getattr(logging, level.upper(), logging.INFO)

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | "
        "%(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(numeric_level)

    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)

    if not root_logger.handlers:
        root_logger.addHandler(console_handler)

        try:
            LOG_DIRECTORY.mkdir(
                parents=True,
                exist_ok=True,
            )
            file_handler = RotatingFileHandler(
                LOG_FILE,
                maxBytes=10 * 1024 * 1024,
                backupCount=5,
                encoding="utf-8",
            )
            file_handler.setFormatter(formatter)
            file_handler.setLevel(numeric_level)
            root_logger.addHandler(file_handler)
        except OSError:
            # In containerized or read-only environments, file logging may be unavailable.
            # Continue with console handler only.
            root_logger.warning(
                "Unable to initialize file handler at %s; continuing with stdout logging only",
                LOG_FILE,
            )
    else:
        # If already configured, ensure log level is aligned
        for handler in root_logger.handlers:
            handler.setLevel(numeric_level)