import logging
import time
import argparse

from app.core.config import settings
from app.core.logging_config import configure_logging
from app.infrastructure.milvus_client import MilvusConnection
from app.infrastructure.milvus_v2_repository import (
    MilvusV2Repository,
)

logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Reset an employee's face embeddings."
    )

    parser.add_argument(
        "--employee-id",
        required=True,
        help="Employee ID.",
    )

    parser.add_argument(
        "--confirm",
        action="store_true",
        help="Confirm deletion.",
    )

    return parser.parse_args()


def main() -> None:
    configure_logging()

    args = parse_args()

    if not args.confirm:
        raise ValueError(
            "Deletion not confirmed. "
            "Use --confirm explicitly."
        )

    connection = MilvusConnection(
        uri=settings.milvus_uri
    )

    try:
        repository = MilvusV2Repository(
            connection.client
        )

        repository.create_collection()

        existing = repository.get_employee_embeddings(
            args.employee_id
        )

        logger.info("======================================")
        logger.info("       Face Profile Reset")
        logger.info("======================================")
        logger.info("Employee ID : %s", args.employee_id)
        logger.info("Existing embeddings count: %d", len(existing))

        if not existing:
            logger.info("No embeddings found for employee %s.", args.employee_id)
            return

        vector_ids = [
            item["vector_id"]
            for item in existing
        ]

        repository.delete_vectors(vector_ids)

        for _ in range(10):
            remaining = repository.get_employee_embeddings(
                args.employee_id
            )

            if not remaining:
                break

            time.sleep(1)

        if remaining:
            logger.error(
                "Face profile reset failed | employee_id=%s | remaining=%d",
                args.employee_id,
                len(remaining),
            )
            raise RuntimeError(
                "Face profile reset failed. "
                f"{len(remaining)} vectors remain."
            )

        logger.info(
            "Face profile deleted successfully | employee_id=%s",
            args.employee_id,
        )

    finally:
        connection.close()


if __name__ == "__main__":
    main()