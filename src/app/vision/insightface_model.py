from insightface.app import FaceAnalysis


class InsightFaceModel:
    def __init__(self) -> None:
        self._model = FaceAnalysis(
            name="buffalo_l",
            allowed_modules=["detection", "recognition"],
            providers=["CPUExecutionProvider"],
        )

        self._model.prepare(
            ctx_id=0,
            det_size=(320, 320)        )

    @property
    def model(self) -> FaceAnalysis:
        return self._model