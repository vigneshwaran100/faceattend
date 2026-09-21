from app.models.face import FaceResult
from app.vision.face_tracker import FaceTracker


def create_face(
    box: tuple[int, int, int, int],
    confidence: float = 0.95,
) -> FaceResult:
    return FaceResult(
        bounding_box=box,
        confidence=confidence,
        embedding=None,  # type: ignore[arg-type]
    )


def test_new_face_creates_track() -> None:
    tracker = FaceTracker()

    tracks = tracker.update([
        create_face((10, 10, 100, 100)),
    ])

    assert len(tracks) == 1
    assert tracks[0].track_id == 1
    assert tracks[0].bounding_box == (10, 10, 100, 100)


def test_same_face_keeps_track_id() -> None:
    tracker = FaceTracker()

    first = tracker.update([
        create_face((10, 10, 100, 100)),
    ])

    second = tracker.update([
        create_face((15, 15, 105, 105)),
    ])

    assert first[0].track_id == second[0].track_id


def test_new_face_gets_new_track_id() -> None:
    tracker = FaceTracker()

    tracker.update([
        create_face((10, 10, 100, 100)),
    ])

    tracks = tracker.update([
        create_face((200, 200, 300, 300)),
    ])

    assert len(tracks) == 2
    assert {track.track_id for track in tracks} == {1, 2}


def test_missing_face_is_removed_after_threshold() -> None:
    tracker = FaceTracker(max_missed_frames=2)

    tracker.update([
        create_face((10, 10, 100, 100)),
    ])

    tracker.update([])
    tracker.update([])

    tracks = tracker.update([])

    assert tracks == []