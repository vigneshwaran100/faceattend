import argparse
import logging

import cv2

from app.core.config import settings
from app.core.logging_config import configure_logging
from app.database.session import SessionFactory
from app.infrastructure.milvus_client import MilvusConnection
from app.infrastructure.milvus_v2_repository import (
    MilvusV2Repository,
)
from app.repositories.employee_repository import (
    EmployeeRepository,
)
from app.services.face_enrollment_service import (
    FaceEnrollmentService,
)
from app.services.face_quality_service import FaceQualityService
from app.vision.camera import Camera
from app.vision.face_engine import FaceEngine
from app.vision.insightface_model import InsightFaceModel

logger = logging.getLogger(__name__)

DETECTION_INTERVAL = 3


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Enroll a face for an existing employee."
    )

    parser.add_argument(
        "--employee-id",
        required=True,
        help="Existing employee ID.",
    )

    return parser.parse_args()


def main() -> None:
    configure_logging()
    args = parse_args()

    # ---------------------------------------------------------
    # 1. Validate employee in PostgreSQL
    # ---------------------------------------------------------

    with SessionFactory() as session:
        employee_repository = EmployeeRepository(session)

        employee = employee_repository.get_by_id(
            args.employee_id
        )

    if employee is None:
        raise ValueError(
            f"Employee does not exist: {args.employee_id}"
        )

    if employee.status != "active":
        raise ValueError(
            f"Employee is not active: {args.employee_id}"
        )

    logger.info("======================================")
    logger.info("       Employee Face Enrollment")
    logger.info("======================================")
    logger.info("Employee ID : %s", employee.employee_id)
    logger.info("Name        : %s", employee.name)
    logger.info("Team        : %s", employee.team_id)
    logger.info("Department  : %s", employee.department_id)
    print()
    print("Move your face slowly:")
    print("front → left → right → up → down")
    print()
    print("Press Q to cancel.")
    print()

    # ---------------------------------------------------------
    # 2. Initialize AI components
    # ---------------------------------------------------------

    model = InsightFaceModel()

    engine = FaceEngine(model.model)

    quality_service = FaceQualityService()

    # ---------------------------------------------------------
    # 3. Initialize Milvus V2
    # ---------------------------------------------------------

    connection = MilvusConnection(
        uri=settings.milvus_uri
    )

    try:
        milvus_repository = MilvusV2Repository(
            connection.client
        )

        milvus_repository.create_collection()

        # -----------------------------------------------------
        # 4. Create enrollment service
        # -----------------------------------------------------

        enrollment_service = FaceEnrollmentService(
            face_engine=engine,
            quality_service=quality_service,
            milvus_repository=milvus_repository,
        )

        collector = enrollment_service.create_collector()

        frame_count = 0
        last_detections = []

        # -----------------------------------------------------
        # 5. Camera guided multi-pose enrollment
        # -----------------------------------------------------

        with Camera() as camera:
            while not collector.is_complete:
                frame = camera.read()
                frame_count += 1

                instruction = enrollment_service.get_current_instruction(
                    collector
                )
                target_pose = enrollment_service.get_current_target_pose(
                    collector
                )
                sample_count = len(collector.samples)

                status_text = instruction
                status_color = (0, 215, 255)

                if frame_count % DETECTION_INTERVAL == 0:
                    last_detections = (
                        enrollment_service.process_frame(
                            frame,
                            collector,
                        )
                    )

                if len(last_detections) == 0:
                    status_text = "Please look at the camera"
                    status_color = (200, 200, 200)
                elif len(last_detections) > 1:
                    status_text = "Multiple faces detected - Stand one at a time"
                    status_color = (0, 165, 255)
                else:
                    detection = last_detections[0]
                    detected_pose = enrollment_service.estimate_pose(
                        detection
                    )

                    if not quality_service.is_acceptable(
                        frame, detection
                    ):
                        status_text = "Please improve lighting / position"
                        status_color = (0, 165, 255)
                    elif (
                        target_pose is not None
                        and detected_pose != target_pose
                    ):
                        status_text = f"{instruction} (Detected: {detected_pose.value})"
                        status_color = (0, 215, 255)
                    else:
                        status_text = f"{instruction} - Hold still..."
                        status_color = (0, 255, 0)

                # -------------------------------------------------
                # Render Clean UI Overlay
                # -------------------------------------------------
                h, w = frame.shape[:2]

                # Top Header Banner
                cv2.rectangle(frame, (0, 0), (w, 55), (20, 20, 20), -1)
                cv2.putText(
                    frame,
                    f"FACE ENROLLMENT | {employee.name} ({employee.employee_id})",
                    (15, 35),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.65,
                    (255, 255, 255),
                    2,
                )

                # Draw bounding box
                for detection in last_detections:
                    x1, y1, x2, y2 = detection.bounding_box
                    x1, y1 = max(0, x1), max(0, y1)
                    x2, y2 = min(w, x2), min(h, y2)
                    cv2.rectangle(
                        frame,
                        (x1, y1),
                        (x2, y2),
                        status_color,
                        2,
                    )

                # Bottom Status Banner
                cv2.rectangle(
                    frame, (0, h - 75), (w, h), (20, 20, 20), -1
                )

                # Instruction and Progress
                progress_text = f"Sample: {sample_count}/{enrollment_service.TARGET_SAMPLES}"
                cv2.putText(
                    frame,
                    progress_text,
                    (15, h - 45),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (180, 180, 180),
                    2,
                )

                cv2.putText(
                    frame,
                    status_text,
                    (15, h - 18),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.65,
                    status_color,
                    2,
                )

                # Progress Bar
                bar_width = 180
                bar_height = 12
                bar_x = w - bar_width - 20
                bar_y = h - 48
                fill_width = int(
                    bar_width
                    * (
                        sample_count
                        / enrollment_service.TARGET_SAMPLES
                    )
                )

                cv2.rectangle(
                    frame,
                    (bar_x, bar_y),
                    (bar_x + bar_width, bar_y + bar_height),
                    (60, 60, 60),
                    -1,
                )
                if fill_width > 0:
                    cv2.rectangle(
                        frame,
                        (bar_x, bar_y),
                        (bar_x + fill_width, bar_y + bar_height),
                        (0, 220, 0),
                        -1,
                    )

                cv2.imshow(
                    "Employee Face Enrollment",
                    frame,
                )

                if cv2.waitKey(1) & 0xFF == ord("q"):
                    print("\n\nEnrollment cancelled.")
                    return

        cv2.destroyAllWindows()

        # ---------------------------------------------------------
        # 6. Store embeddings in Milvus V2
        # ---------------------------------------------------------

        print("\n\nSaving face embeddings...")

        saved_count = enrollment_service.save_samples(
            employee,
            collector,
        )

        print()
        print("======================================")
        print("    Face Enrollment Completed")
        print("======================================")
        print(f"Employee ID : {employee.employee_id}")
        print(f"Name        : {employee.name}")
        print(f"Samples     : {saved_count}")
        print(f"Storage     : {milvus_repository.COLLECTION_NAME}")
        print("======================================")
        print()

    finally:
        cv2.destroyAllWindows()
        connection.close()


if __name__ == "__main__":
    main()