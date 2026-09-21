from dataclasses import dataclass

from app.models.face import FaceDetection
from app.vision.iou import BoundingBox, calculate_iou


@dataclass
class TrackedFace:
    track_id: int
    bounding_box: BoundingBox
    confidence: float
    missed_frames: int = 0


class FaceTracker:
    def __init__(
        self,
        iou_threshold: float = 0.5,
        max_missed_frames: int = 5,
    ) -> None:
        self._iou_threshold = iou_threshold
        self._max_missed_frames = max_missed_frames

        self._tracks: dict[int, TrackedFace] = {}
        self._next_track_id = 1

    def update(
        self,
        detections: list[FaceDetection],
    ) -> list[TrackedFace]:
        matched_track_ids: set[int] = set()

        for detection in detections:
            best_track_id: int | None = None
            best_iou = 0.0

            for track_id, track in self._tracks.items():
                if track_id in matched_track_ids:
                    continue

                iou = calculate_iou(
                    track.bounding_box,
                    detection.bounding_box,
                )

                if iou > best_iou:
                    best_iou = iou
                    best_track_id = track_id

            if (
                best_track_id is not None
                and best_iou >= self._iou_threshold
            ):
                track = self._tracks[best_track_id]

                track.bounding_box = detection.bounding_box
                track.confidence = detection.confidence
                track.missed_frames = 0

                matched_track_ids.add(best_track_id)

            else:
                track = TrackedFace(
                    track_id=self._next_track_id,
                    bounding_box=detection.bounding_box,
                    confidence=detection.confidence,
                )

                self._tracks[self._next_track_id] = track
                matched_track_ids.add(self._next_track_id)

                self._next_track_id += 1

        for track_id, track in list(self._tracks.items()):
            if track_id not in matched_track_ids:
                track.missed_frames += 1

                if track.missed_frames > self._max_missed_frames:
                    del self._tracks[track_id]

        return list(self._tracks.values())