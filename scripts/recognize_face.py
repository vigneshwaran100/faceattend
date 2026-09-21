import logging
import cv2
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from app.core.config import settings
from app.core.logging_config import configure_logging
from app.database.session import SessionFactory
from app.infrastructure.milvus_client import MilvusConnection
from app.infrastructure.milvus_v2_repository import (
    MilvusV2Repository,
)
from app.repositories.attendance_repository import (
    AttendanceRepository,
)
from app.services.attendance_service import (
    AttendanceService,
)
from app.services.face_recognition_service import (
    FaceRecognitionService,
)
from app.vision.camera import Camera
from app.vision.face_engine import FaceEngine
from app.vision.insightface_model import InsightFaceModel


IST = ZoneInfo("Asia/Kolkata")
DETECTION_INTERVAL = 3
RECOGNITION_COOLDOWN_SECONDS = 30
logger = logging.getLogger(__name__)


def main() -> None:
    configure_logging()

    logger.info("======================================")
    logger.info("       Face Recognition Started")
    logger.info("======================================")
    logger.info("Press Q to exit.")

    # AI MODEL
    model = InsightFaceModel()
    engine = FaceEngine(model.model)

    # MILVUS CONNECTION
    milvus_connection = MilvusConnection(
        uri=settings.milvus_uri
    )

    # POSTGRESQL SESSION
    session = SessionFactory()

    try:
        # MILVUS REPOSITORY
        milvus_repository = MilvusV2Repository(
            milvus_connection.client
        )
        milvus_repository.create_collection()

        # FACE RECOGNITION SERVICE
        recognition_service = FaceRecognitionService(
            repository=milvus_repository,
            threshold=settings.face_similarity_threshold,
        )

        # ATTENDANCE REPOSITORY
        attendance_repository = AttendanceRepository(
            session
        )

        # ATTENDANCE SERVICE
        attendance_service = AttendanceService(
            repository=attendance_repository,
        )

        frame_count = 0
        last_detections = []
        last_results = []
        last_processed_at: dict[str, datetime] = {}

        with Camera() as camera:
            while True:
                frame = camera.read()

                frame_count += 1

                # RUN DETECTION EVERY N FRAMES
                if frame_count % DETECTION_INTERVAL == 0:
                    (
                        last_detections,
                        embeddings,
                    ) = engine.process(frame)

                    last_results = []

                    for embedding in embeddings:
                        result = recognition_service.recognize(
                            embedding.vector
                        )

                        last_results.append(result)

                        if not result.recognized:
                            logger.warning(
                                "Unknown face detected | similarity=%.3f",
                                result.similarity,
                            )
                            continue

                        current_time = datetime.now(
                            IST
                        )

                        last_processed = last_processed_at.get(
                            result.employee_id
                        )

                        if (
                            last_processed is not None
                            and current_time - last_processed
                            < timedelta(
                                seconds=RECOGNITION_COOLDOWN_SECONDS
                            )
                        ):
                            logger.debug(
                                "Recognition ignored due to cooldown | employee_id=%s",
                                result.employee_id,
                            )
                            continue

                        last_processed_at[
                            result.employee_id
                        ] = current_time

                        logger.info(
                            "Face recognized | employee_id=%s | similarity=%.3f",
                            result.employee_id,
                            result.similarity,
                        )

                        if settings.scanner_mode == "check_in":
                            attendance = attendance_service.check_in(
                                result.employee_id
                            )

                            if attendance.check_in is not None:
                                logger.info(
                                    "CHECK-IN: %s | Time: %s | Status: %s",
                                    attendance.employee_id,
                                    attendance.check_in,
                                    attendance.status,
                                )

                        elif settings.scanner_mode == "check_out":
                            try:
                                attendance = attendance_service.check_out(
                                    result.employee_id
                                )

                                logger.info(
                                    "CHECK-OUT UPDATED: %s | Check-in: %s | Check-out: %s | Status: %s",
                                    attendance.employee_id,
                                    attendance.check_in,
                                    attendance.check_out,
                                    attendance.status,
                                )

                            except ValueError as exc:
                                logger.error(
                                    "Attendance error: %s",
                                    exc,
                                )

                # ----------------------------------------------
                # DRAW DETECTIONS
                # ----------------------------------------------
                for index, detection in enumerate(
                    last_detections
                ):
                    x1, y1, x2, y2 = (
                        detection.bounding_box
                    )

                    if index < len(last_results):
                        result = last_results[index]

                        if result.recognized:
                            label = (
                                f"{result.employee_id} "
                                f"{result.similarity:.2f}"
                            )
                        else:
                            label = (
                                f"Unknown "
                                f"{result.similarity:.2f}"
                            )
                    else:
                        label = "Processing..."

                    cv2.rectangle(
                        frame,
                        (x1, y1),
                        (x2, y2),
                        (0, 255, 0),
                        2,
                    )

                    cv2.putText(
                        frame,
                        label,
                        (
                            x1,
                            max(y1 - 10, 20),
                        ),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.6,
                        (0, 255, 0),
                        2,
                    )

                # ----------------------------------------------
                # UI INFORMATION
                # ----------------------------------------------
                cv2.putText(
                    frame,
                    "Face Recognition",
                    (20, 30),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 255, 0),
                    2,
                )

                cv2.putText(
                    frame,
                    "Press Q to exit",
                    (20, 60),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (0, 255, 0),
                    2,
                )

                cv2.imshow(
                    "Face Recognition",
                    frame,
                )

                # EXIT
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break

    finally:
        cv2.destroyAllWindows()
        session.close()
        milvus_connection.close()


if __name__ == "__main__":
    main()