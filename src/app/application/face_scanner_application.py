import logging
import time

import cv2
import numpy as np

from app.core.config import settings
from app.database.session import SessionFactory
from app.infrastructure.milvus_client import MilvusConnection
from app.infrastructure.milvus_v2_repository import (
    MilvusV2Repository,
)
from app.models.scanner_type import ScannerType
from app.repositories.attendance_repository import (
    AttendanceRepository,
)
from app.repositories.employee_repository import (
    EmployeeRepository,
)
from app.repositories.scanner_audit_repository import (
    ScannerAuditRepository,
)
from app.services.attendance_service import AttendanceService
from app.services.face_quality_service import FaceQualityService
from app.services.face_recognition_service import (
    FaceRecognitionService,
)
from app.services.recognition_cooldown import RecognitionCooldown
from app.services.recognition_stability_service import (
    RecognitionStabilityService,
)
from app.services.scanner_audit_service import (
    ScannerAuditService,
)
from app.services.scanner_orchestration_service import (
    ScannerOrchestrationService,
)
from app.vision.camera import Camera
from app.vision.insightface_model import InsightFaceModel
from app.vision.face_engine import FaceEngine


logger = logging.getLogger(__name__)


class FaceScannerApplication:
    def __init__(
        self,
        scanner_type: ScannerType,
        detection_interval: int = 3,
        scan_cooldown_seconds: int = 60,
        required_consecutive_matches: int = 5,
    ) -> None:
        self._scanner_type = scanner_type
        self._detection_interval = detection_interval
        self._scan_cooldown_seconds = scan_cooldown_seconds
        self._required_consecutive_matches = (
            required_consecutive_matches
        )

    def run(self) -> None:
        milvus_connection = None
        session = None

        try:
            logger.info(
                "Face scanner starting | scanner_type=%s",
                self._scanner_type.value,
            )

            model = InsightFaceModel()
            engine = FaceEngine(model.model)

            milvus_connection = MilvusConnection(
                uri=settings.milvus_uri,
            )
            session = SessionFactory()

            milvus_repository = MilvusV2Repository(
                milvus_connection.client
            )

            recognition_service = FaceRecognitionService(
                repository=milvus_repository,
                threshold=settings.face_similarity_threshold,
            )

            attendance_repository = AttendanceRepository(session)
            employee_repository = EmployeeRepository(session)
            audit_repository = ScannerAuditRepository(session)

            attendance_service = AttendanceService(
                repository=attendance_repository,
            )

            audit_service = ScannerAuditService(
                repository=audit_repository,
            )

            quality_service = FaceQualityService()

            recognition_stability_service = (
                RecognitionStabilityService(
                    required_matches=(
                        self._required_consecutive_matches
                    ),
                )
            )

            recognition_cooldown = RecognitionCooldown(
                cooldown_seconds=self._scan_cooldown_seconds,
            )

            orchestration_service = (
                ScannerOrchestrationService(
                    attendance_service=attendance_service,
                    recognition_stability_service=(
                        recognition_stability_service
                    ),
                    recognition_cooldown=recognition_cooldown,
                    employee_repository=employee_repository,
                    scanner_audit_service=audit_service,
                )
            )

            logger.info(
                "Face scanner initialized successfully | "
                "scanner_type=%s",
                self._scanner_type.value,
            )

            self._run_camera_loop(
                engine=engine,
                recognition_service=recognition_service,
                orchestration_service=orchestration_service,
                recognition_cooldown=recognition_cooldown,
                quality_service=quality_service,
                audit_service=audit_service,
            )

        except KeyboardInterrupt:
            logger.info(
                "Shutdown requested by user | scanner_type=%s",
                self._scanner_type.value,
            )

        finally:
            logger.info("Scanner cleanup started")

            cv2.destroyAllWindows()

            if session is not None:
                session.close()
                logger.info("Database session closed")

            if milvus_connection is not None:
                milvus_connection.close()
                logger.info("Milvus connection closed")

            logger.info(
                "Face scanner stopped safely | scanner_type=%s",
                self._scanner_type.value,
            )

    def _run_camera_loop(
        self,
        engine,
        recognition_service,
        orchestration_service,
        recognition_cooldown: RecognitionCooldown,
        quality_service: FaceQualityService,
        audit_service: ScannerAuditService,
    ) -> None:
        frame_count = 0
        last_detections = []
        status_message = "Please look at the camera"
        status_color = (220, 220, 220)
        box_label = None
        box_color = (0, 220, 0)

        success_hold_until = 0.0
        success_employee_id: str | None = None
        action_text = (
            "Check-in"
            if self._scanner_type == ScannerType.CHECK_IN
            else "Check-out"
        )

        with Camera() as camera:
            while True:
                frame = camera.read()
                frame_count += 1
                current_time = time.time()

                # If recently processed successfully, maintain success display
                if current_time < success_hold_until and success_employee_id:
                    status_message = f"✓ {action_text} successful ({success_employee_id})"
                    status_color = (0, 220, 0)
                    box_label = success_employee_id
                    box_color = (0, 220, 0)

                elif frame_count % self._detection_interval == 0:
                    (
                        last_detections,
                        embeddings,
                    ) = engine.process(frame)

                    face_count = len(embeddings)

                    # Rule 1: No face -> reset stability & neutral prompt
                    if face_count == 0:
                        orchestration_service.process(
                            employee_id=None,
                            scanner_type=self._scanner_type,
                        )
                        status_message = "Please look at the camera"
                        status_color = (220, 220, 220)
                        box_label = None
                        box_color = (220, 220, 220)

                    # Rule 2: Multiple faces -> block recognition
                    elif face_count > 1:
                        orchestration_service.process(
                            employee_id=None,
                            scanner_type=self._scanner_type,
                        )

                        logger.warning(
                            "Multiple faces detected. "
                            "Please stand one at a time."
                        )

                        audit_service.log_event(
                            scanner_type=self._scanner_type,
                            event_type="multiple_faces",
                            status="FAILURE",
                            message="Multiple faces detected",
                        )

                        status_message = "Please stand one at a time"
                        status_color = (0, 165, 255)
                        box_label = "Multiple Faces"
                        box_color = (0, 165, 255)

                    # Rule 3: Exactly one face -> check quality and recognize
                    else:
                        detection = last_detections[0]
                        quality_result = quality_service.check_quality(
                            frame, detection
                        )

                        if not quality_result.acceptable:
                            orchestration_service.process(
                                employee_id=None,
                                scanner_type=self._scanner_type,
                            )

                            if quality_result.reason == "blur":
                                logger.warning(
                                    "Face quality failed | reason=blur | score=%.2f (min=%.2f)",
                                    quality_result.blur_score,
                                    quality_result.min_blur_score,
                                )
                            elif quality_result.reason == "face_size":
                                logger.warning(
                                    "Face quality failed | reason=face_size | width=%d | height=%d (min=%dpx)",
                                    quality_result.width,
                                    quality_result.height,
                                    quality_result.min_face_size,
                                )
                            elif quality_result.reason == "confidence":
                                logger.warning(
                                    "Face quality failed | reason=confidence | confidence=%.3f (min=%.2f)",
                                    quality_result.confidence,
                                    quality_result.min_confidence,
                                )
                            else:
                                logger.warning(
                                    "Face quality failed | %s",
                                    quality_result.details,
                                )

                            audit_service.log_event(
                                scanner_type=self._scanner_type,
                                event_type="quality_failure",
                                status="FAILURE",
                                message=f"Face quality failed | {quality_result.details}",
                            )

                            status_message = "Please improve your position / lighting"
                            status_color = (0, 165, 255)
                            box_label = "Adjust Position"
                            box_color = (0, 165, 255)

                        else:
                            embedding = embeddings[0]

                            result = recognition_service.recognize(
                                embedding.vector
                            )

                            if not result.recognized:
                                orchestration_service.process(
                                    employee_id=None,
                                    scanner_type=self._scanner_type,
                                )

                                logger.warning(
                                    "Unknown face detected | similarity=%.3f",
                                    result.similarity,
                                )

                                audit_service.log_event(
                                    scanner_type=self._scanner_type,
                                    event_type="unknown_face",
                                    status="FAILURE",
                                    similarity=result.similarity,
                                    message=(
                                        f"Face not recognized (similarity: "
                                        f"{result.similarity:.2f})"
                                    ),
                                )
                                status_message = "Unknown face - Please try again"
                                status_color = (0, 0, 255)
                                box_label = "Unknown"
                                box_color = (0, 0, 255)

                            else:
                                employee_id = result.employee_id

                                # If recognized employee is in cooldown, show calm status without repeating DB writes
                                if not recognition_cooldown.can_process(
                                    employee_id
                                ):
                                    status_message = f"Attendance already recorded ({employee_id})"
                                    status_color = (255, 191, 0)
                                    box_label = employee_id
                                    box_color = (255, 191, 0)

                                else:
                                    processing_result = (
                                        orchestration_service.process(
                                            employee_id=employee_id,
                                            scanner_type=self._scanner_type,
                                        )
                                    )

                                    if processing_result.success:
                                        logger.info(
                                            "%s SUCCESS | employee_id=%s | message=%s",
                                            self._scanner_type.value.upper(),
                                            processing_result.employee_id,
                                            processing_result.message,
                                        )
                                        success_hold_until = (
                                            time.time() + 3.0
                                        )
                                        success_employee_id = (
                                            result.employee_id
                                        )
                                        status_message = f"✓ {action_text} successful ({result.employee_id})"
                                        status_color = (0, 220, 0)
                                        box_label = result.employee_id
                                        box_color = (0, 220, 0)

                                    elif (
                                        processing_result.message
                                        == "Recognition not yet stable"
                                    ):
                                        logger.info(
                                            "Waiting for stable recognition | "
                                            "employee_id=%s",
                                            result.employee_id,
                                        )
                                        status_message = (
                                            "Hold still..."
                                        )
                                        status_color = (0, 215, 255)
                                        box_label = "Hold still..."
                                        box_color = (0, 215, 255)

                                    elif (
                                        processing_result.message
                                        == "Recognition cooldown active"
                                    ):
                                        logger.info(
                                            "Recognition ignored due to cooldown | "
                                            "employee_id=%s",
                                            result.employee_id,
                                        )
                                        status_message = f"Attendance already recorded ({result.employee_id})"
                                        status_color = (255, 191, 0)
                                        box_label = result.employee_id
                                        box_color = (255, 191, 0)

                                    elif (
                                        processing_result.message
                                        == "Employee is inactive"
                                    ):
                                        status_message = (
                                            "Employee is inactive"
                                        )
                                        status_color = (0, 0, 255)
                                        box_label = "Inactive"
                                        box_color = (0, 0, 255)

                                    elif (
                                        processing_result.message
                                        == "Employee not found"
                                    ):
                                        status_message = "Employee not found in records"
                                        status_color = (0, 0, 255)
                                        box_label = "Not Found"
                                        box_color = (0, 0, 255)

                                    else:
                                        logger.error(
                                            "Attendance processing failed | "
                                            "employee_id=%s | message=%s",
                                            processing_result.employee_id,
                                            processing_result.message,
                                        )
                                        status_message = "Unable to process - Please try again"
                                        status_color = (0, 0, 255)
                                        box_label = "Error"
                                        box_color = (0, 0, 255)

                self._render_ui(
                    frame=frame,
                    status_message=status_message,
                    status_color=status_color,
                    detections=last_detections,
                    box_label=box_label,
                    box_color=box_color,
                )

                scanner_title = (
                    f"{self._scanner_type.value.upper()} SCANNER"
                )
                cv2.imshow(
                    scanner_title,
                    frame,
                )

                if cv2.waitKey(1) & 0xFF == ord("q"):
                    logger.info(
                        "Scanner exit requested | scanner_type=%s",
                        self._scanner_type.value,
                    )
                    break

    def _render_ui(
        self,
        frame: np.ndarray,
        status_message: str,
        status_color: tuple[int, int, int],
        detections: list,
        box_label: str | None,
        box_color: tuple[int, int, int],
    ) -> None:
        height, width = frame.shape[:2]

        # Draw detected face boxes and badges
        for detection in detections:
            x1, y1, x2, y2 = detection.bounding_box
            cv2.rectangle(
                frame,
                (x1, y1),
                (x2, y2),
                box_color,
                2,
            )

            if box_label:
                (text_w, text_h), _ = cv2.getTextSize(
                    box_label,
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.55,
                    2,
                )
                tag_y1 = max(y1 - text_h - 10, 52)
                tag_y2 = tag_y1 + text_h + 8
                tag_x2 = min(x1 + text_w + 12, width - 5)

                cv2.rectangle(
                    frame,
                    (x1, tag_y1),
                    (tag_x2, tag_y2),
                    box_color,
                    cv2.FILLED,
                )
                cv2.putText(
                    frame,
                    box_label,
                    (x1 + 6, tag_y2 - 5),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.55,
                    (0, 0, 0) if box_color != (0, 0, 0) else (255, 255, 255),
                    2,
                )

        # Header Bar Overlay
        header_overlay = frame.copy()
        cv2.rectangle(
            header_overlay,
            (0, 0),
            (width, 46),
            (25, 25, 25),
            cv2.FILLED,
        )
        cv2.rectangle(
            header_overlay,
            (0, height - 52),
            (width, height),
            (25, 25, 25),
            cv2.FILLED,
        )
        cv2.addWeighted(
            header_overlay,
            0.75,
            frame,
            0.25,
            0,
            frame,
        )

        # Header Text
        scanner_title = f"{self._scanner_type.value.upper()} SCANNER"
        cv2.putText(
            frame,
            scanner_title,
            (18, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            (255, 255, 255),
            2,
        )
        cv2.putText(
            frame,
            "Press Q to exit",
            (max(width - 150, 20), 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (170, 170, 170),
            1,
        )

        # Bottom Status Message with Status Dot Indicator
        (msg_w, _), _ = cv2.getTextSize(
            status_message,
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            2,
        )
        msg_x = max((width - msg_w) // 2, 28)
        msg_y = height - 19

        cv2.circle(
            frame,
            (msg_x - 14, msg_y - 6),
            5,
            status_color,
            cv2.FILLED,
        )
        cv2.putText(
            frame,
            status_message,
            (msg_x, msg_y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            status_color,
            2,
        )