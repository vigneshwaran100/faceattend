import cv2

from app.vision.camera import Camera


def main() -> None:
    with Camera() as camera:
        while True:
            frame = camera.read()

            cv2.imshow("Face Recognition Camera", frame)

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()