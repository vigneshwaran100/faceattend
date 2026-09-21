import logging
from datetime import datetime, timezone
from time import time_ns

import cv2
import numpy as np

from app.infrastructure.milvus_v2_repository import MilvusV2Repository
from app.models.employee import Employee
from app.models.face import FaceDetection
from app.models.face_pose import FacePose
from app.services.face_sample_collector import FaceSampleCollector
from app.services.face_quality_service import FaceQualityService
from app.vision.face_engine import FaceEngine

logger = logging.getLogger(__name__)


class FaceEnrollmentService:
    TARGET_SAMPLES = 10
    DUPLICATE_THRESHOLD = 0.98
    MODEL_NAME = "w600k_r50"
    MODEL_VERSION = "buffalo_l"
    EMBEDDING_VERSION = "1"

    GUIDED_POSES: list[tuple[FacePose, str]] = [
        (FacePose.FRONT, "Look Straight"),
        (FacePose.FRONT, "Look Straight"),
        (FacePose.LEFT, "Turn Left"),
        (FacePose.LEFT, "Turn Left"),
        (FacePose.RIGHT, "Turn Right"),
        (FacePose.RIGHT, "Turn Right"),
        (FacePose.UP, "Look Up"),
        (FacePose.UP, "Look Up"),
        (FacePose.DOWN, "Look Down"),
        (FacePose.DOWN, "Look Down"),
    ]

    def __init__(
        self,
        face_engine: FaceEngine,
        quality_service: FaceQualityService,
        milvus_repository: MilvusV2Repository,
    ) -> None:
        self._face_engine = face_engine
        self._quality_service = quality_service
        self._milvus_repository = milvus_repository

    def create_collector(self) -> FaceSampleCollector:
        return FaceSampleCollector(
            target_samples=self.TARGET_SAMPLES,
            duplicate_threshold=self.DUPLICATE_THRESHOLD,
        )

    def get_current_instruction(
        self,
        collector: FaceSampleCollector,
    ) -> str:
        index = len(collector.samples)
        if index >= len(self.GUIDED_POSES):
            return "Enrollment Complete"
        return self.GUIDED_POSES[index][1]

    def get_current_target_pose(
        self,
        collector: FaceSampleCollector,
    ) -> FacePose | None:
        index = len(collector.samples)
        if index >= len(self.GUIDED_POSES):
            return None
        return self.GUIDED_POSES[index][0]

    @staticmethod
    def estimate_pose(detection: FaceDetection) -> FacePose:
        # 1. Check estimated pose angles [pitch, yaw, roll] if available
        pose = getattr(detection, "pose", None)
        if isinstance(pose, (tuple, list, np.ndarray)) and len(pose) >= 2:
            try:
                pitch, yaw = float(pose[0]), float(pose[1])
                if abs(yaw) > 12.0:
                    return FacePose.RIGHT if yaw > 12.0 else FacePose.LEFT
                if abs(pitch) > 10.0:
                    return FacePose.DOWN if pitch > 10.0 else FacePose.UP
                return FacePose.FRONT
            except (TypeError, ValueError):
                pass

        # 2. Check 5-point facial keypoints if available
        landmarks = getattr(detection, "landmarks", None)
        if isinstance(landmarks, (list, np.ndarray)) and len(landmarks) >= 5:
            try:
                left_eye, right_eye, nose = (
                    landmarks[0],
                    landmarks[1],
                    landmarks[2],
                )
                left_mouth, right_mouth = landmarks[3], landmarks[4]

                eye_width = max(
                    float(right_eye[0] - left_eye[0]), 1.0
                )
                dist_left = float(nose[0] - left_eye[0])
                dist_right = float(right_eye[0] - nose[0])
                yaw_ratio = (dist_left - dist_right) / eye_width

                if yaw_ratio > 0.18:
                    return FacePose.RIGHT
                if yaw_ratio < -0.18:
                    return FacePose.LEFT

                eye_mid_y = float(left_eye[1] + right_eye[1]) / 2.0
                mouth_mid_y = float(left_mouth[1] + right_mouth[1]) / 2.0
                face_height = max(mouth_mid_y - eye_mid_y, 1.0)
                nose_rel_y = float(nose[1] - eye_mid_y) / face_height

                if nose_rel_y < 0.42:
                    return FacePose.UP
                if nose_rel_y > 0.68:
                    return FacePose.DOWN

                return FacePose.FRONT
            except (TypeError, ValueError, IndexError):
                pass

        return FacePose.FRONT

    def process_frame(
        self,
        frame: np.ndarray,
        collector: FaceSampleCollector,
    ) -> list[FaceDetection]:
        detections, embeddings = self._face_engine.process(frame)

        if len(detections) != 1 or len(embeddings) != 1:
            return detections

        detection = detections[0]
        embedding = embeddings[0]

        if not self._quality_service.is_acceptable(
            frame,
            detection,
        ):
            return detections

        target_pose = self.get_current_target_pose(collector)
        detected_pose = self.estimate_pose(detection)

        if target_pose is not None and detected_pose != target_pose:
            return detections

        collector.add(embedding.vector)
        return detections

    def save_samples(
        self,
        employee: Employee,
        collector: FaceSampleCollector,
    ) -> int:
        if not collector.is_complete:
            raise ValueError(
                "Face enrollment is incomplete"
            )

        old_embeddings = (
            self._milvus_repository.get_employee_embeddings(
                employee.employee_id
            )
        )

        old_vector_ids = [
            item["vector_id"]
            for item in old_embeddings
        ]

        created_at = int(
            datetime.now(timezone.utc).timestamp()
        )

        inserted_vector_ids: list[int] = []

        try:
            for index, sample in enumerate(
                collector.samples,
                start=1,
            ):
                vector_id = time_ns() + index

                embedding = np.asarray(
                    sample.embedding,
                    dtype=np.float32,
                )

                self._milvus_repository.insert_embedding(
                    vector_id=vector_id,
                    employee_id=employee.employee_id,
                    embedding=embedding.tolist(),
                    model_name=self.MODEL_NAME,
                    model_version=self.MODEL_VERSION,
                    embedding_version=self.EMBEDDING_VERSION,
                    created_at=created_at,
                )

                inserted_vector_ids.append(vector_id)

            # New profile is fully stored.
            # Now remove the old profile.
            self._milvus_repository.delete_vectors(
                old_vector_ids
            )

            logger.info(
                "Face enrollment completed | employee_id=%s | vectors_saved=%d",
                employee.employee_id,
                len(inserted_vector_ids),
            )

        except Exception:
            # Remove only partially inserted NEW vectors.
            logger.exception(
                "Face enrollment storage failed | employee_id=%s",
                employee.employee_id,
            )
            self._milvus_repository.delete_vectors(
                inserted_vector_ids
            )
            raise

        return len(inserted_vector_ids)

    def enroll_image(
        self,
        employee: Employee,
        image_bytes: bytes,
    ) -> int:
        if not image_bytes or len(image_bytes) == 0:
            raise ValueError("Uploaded image is empty")

        try:
            nparr = np.frombuffer(image_bytes, np.uint8)
            if nparr.size == 0:
                raise ValueError("Uploaded image is empty")
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        except Exception as error:
            if isinstance(error, ValueError):
                raise
            raise ValueError(
                f"Invalid or corrupted image format: {error}"
            ) from error

        if frame is None or frame.size == 0:
            raise ValueError("Invalid or unreadable image format")

        detections, embeddings = self._face_engine.process(frame)

        if len(detections) == 0:
            raise ValueError(
                "No face detected in the provided image. Please ensure the face is clearly visible"
            )

        if len(detections) > 1:
            raise ValueError(
                "Multiple faces detected. Please provide an image with exactly one face"
            )

        detection = detections[0]
        embedding = embeddings[0]

        if not self._quality_service.is_acceptable(
            frame,
            detection,
        ):
            if hasattr(self._quality_service, "check_quality"):
                try:
                    result = self._quality_service.check_quality(
                        frame,
                        detection,
                    )
                    if hasattr(result, "reason"):
                        if result.reason == "blur":
                            raise ValueError(
                                "Face quality check failed: image is blurry. Please provide a clear, sharp photo"
                            )
                        if result.reason == "face_size":
                            raise ValueError(
                                f"Face quality check failed: face size is too small (minimum {result.min_face_size}px required)"
                            )
                        if result.reason == "confidence":
                            raise ValueError(
                                f"Face quality check failed: detection confidence ({result.confidence:.2f}) is below threshold ({result.min_confidence:.2f})"
                            )
                except ValueError:
                    raise
                except Exception:
                    pass

            raise ValueError(
                "Face quality check failed. Ensure the face is clear, well-lit, and facing forward"
            )

        old_embeddings = (
            self._milvus_repository.get_employee_embeddings(
                employee.employee_id
            )
        )

        old_vector_ids = [
            item["vector_id"]
            for item in old_embeddings
        ]

        created_at = int(
            datetime.now(timezone.utc).timestamp()
        )

        vector_id = time_ns()
        emb_vector = np.asarray(
            embedding.vector,
            dtype=np.float32,
        )

        inserted_vector_ids: list[int] = []

        try:
            self._milvus_repository.insert_embedding(
                vector_id=vector_id,
                employee_id=employee.employee_id,
                embedding=emb_vector.tolist(),
                model_name=self.MODEL_NAME,
                model_version=self.MODEL_VERSION,
                embedding_version=self.EMBEDDING_VERSION,
                created_at=created_at,
            )
            inserted_vector_ids.append(vector_id)

            if old_vector_ids:
                self._milvus_repository.delete_vectors(
                    old_vector_ids
                )

            logger.info(
                "Single face image enrolled successfully | employee_id=%s | vector_id=%d",
                employee.employee_id,
                vector_id,
            )

        except Exception:
            logger.exception(
                "Face image enrollment storage failed | employee_id=%s",
                employee.employee_id,
            )
            if inserted_vector_ids:
                self._milvus_repository.delete_vectors(
                    inserted_vector_ids
                )
            raise

        return 1

    def enroll_samples(
        self,
        employee: Employee,
        image_bytes_list: list[bytes],
    ) -> int:
        if len(image_bytes_list) != self.TARGET_SAMPLES:
            raise ValueError(
                f"Exactly {self.TARGET_SAMPLES} face sample images are required, received {len(image_bytes_list)}"
            )

        collector = self.create_collector()

        for index, image_bytes in enumerate(image_bytes_list, start=1):
            if not image_bytes or len(image_bytes) == 0:
                raise ValueError(f"Sample {index}: Uploaded image is empty")

            try:
                nparr = np.frombuffer(image_bytes, np.uint8)
                if nparr.size == 0:
                    raise ValueError(f"Sample {index}: Uploaded image is empty")
                frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            except Exception as error:
                if isinstance(error, ValueError):
                    raise
                raise ValueError(
                    f"Sample {index}: Invalid or corrupted image format: {error}"
                ) from error

            if frame is None or frame.size == 0:
                raise ValueError(
                    f"Sample {index}: Invalid or unreadable image format"
                )

            detections, embeddings = self._face_engine.process(frame)

            if len(detections) == 0:
                raise ValueError(
                    f"Sample {index}: No face detected in the provided image. Please ensure the face is clearly visible"
                )

            if len(detections) > 1:
                raise ValueError(
                    f"Sample {index}: Multiple faces detected ({len(detections)}). Please provide an image with exactly one face"
                )

            detection = detections[0]
            embedding = embeddings[0]

            if not self._quality_service.is_acceptable(
                frame,
                detection,
            ):
                if hasattr(self._quality_service, "check_quality"):
                    try:
                        result = self._quality_service.check_quality(
                            frame,
                            detection,
                        )
                        if hasattr(result, "reason"):
                            if result.reason == "blur":
                                raise ValueError(
                                    f"Sample {index}: Face quality check failed: image is blurry. Please provide a clear, sharp photo"
                                )
                            if result.reason == "face_size":
                                raise ValueError(
                                    f"Sample {index}: Face quality check failed: face size is too small (minimum {result.min_face_size}px required)"
                                )
                            if result.reason == "confidence":
                                raise ValueError(
                                    f"Sample {index}: Face quality check failed: detection confidence ({result.confidence:.2f}) is below threshold ({result.min_confidence:.2f})"
                                )
                    except ValueError:
                        raise
                    except Exception:
                        pass

                raise ValueError(
                    f"Sample {index}: Face quality check failed. Ensure the face is clear, well-lit, and facing forward"
                )

            normalized_vec = collector._normalize(embedding.vector)
            if collector._is_duplicate(normalized_vec):
                raise ValueError(
                    f"Sample {index}: Duplicate face image detected. Each of the {self.TARGET_SAMPLES} samples must be a distinct pose or capture"
                )

            added = collector.add(embedding.vector)
            if not added:
                raise ValueError(
                    f"Sample {index}: Failed to add sample to collector"
                )

        if not collector.is_complete:
            raise ValueError(
                f"Face enrollment incomplete: expected {self.TARGET_SAMPLES} samples, collected {len(collector.samples)}"
            )

        return self.save_samples(employee, collector)