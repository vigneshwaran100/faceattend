import time

import cv2
import numpy as np

from app.vision.camera import Camera
from app.vision.face_engine import FaceEngine
from app.vision.insightface_model import InsightFaceModel

DETECTION_INTERVAL=3

def main() -> None:
    model = InsightFaceModel()
    engine = FaceEngine(model.model)

    total_frames = 0
    total_inference_time = 0.0
    inference_frames = 0
    frame_count = 0
    last_faces = []
    start_time = time.perf_counter()
    with Camera() as camera:
        while True:
            frame = camera.read()
            frame_count += 1
            total_frames += 1

            # Run AI inference only every 3rd frame
            if frame_count % DETECTION_INTERVAL == 0:
                inference_start = time.perf_counter()

                last_faces = engine.process(frame)

                inference_time = time.perf_counter() - inference_start

                total_inference_time += inference_time
                inference_frames += 1

            faces = last_faces

            for face in faces:
                x1, y1, x2, y2 = face.bounding_box

                cv2.rectangle(
                    frame,
                    (x1, y1),
                    (x2, y2),
                    (0, 255, 0),
                    2,
                )

                label = f"Face {face.confidence:.2f}"

                cv2.putText(
                    frame,
                    label,
                    (x1, max(y1 - 10, 20)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (0, 255, 0),
                    2,
                )

            # FPS calculation
            elapsed_time = time.perf_counter() - start_time
            fps = total_frames / elapsed_time

            average_inference_ms = (
                total_inference_time / inference_frames
            ) * 1000 if inference_frames > 0 else 0.0

            cv2.putText(
                frame,
                f"FPS: {fps:.2f}",
                (20, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 0),
                2,
            )

            cv2.putText(
                frame,
                f"Inference: {average_inference_ms:.2f} ms",
                (20, 60),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 0),
                2,
            )

            cv2.putText(
                frame,
                f"Faces: {len(faces)}",
                (20, 90),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 0),
                2,
            )

            cv2.imshow("Face Engine Benchmark", frame)

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
            
    cv2.destroyAllWindows()

    if total_frames > 0:
        total_elapsed = time.perf_counter() - start_time

        print("\n========== Benchmark ==========")
        print(f"Total frames       : {total_frames}")
        print(f"Total time         : {total_elapsed:.2f} sec")
        print(f"Average FPS        : {total_frames / total_elapsed:.2f}")
        print(
            f"Average inference  : "
            f"{(total_inference_time / total_frames) * 1000:.2f} ms"
        )
        print("===============================\n")


if __name__ == "__main__":
    main()