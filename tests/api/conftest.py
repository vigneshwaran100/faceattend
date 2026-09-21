"""
API test conftest — stubs out heavy ML/vision modules so tests can be
collected and run without GPU dependencies (insightface, onnxruntime, etc.).

The actual FaceEngine, InsightFaceModel, and FaceQualityService are always
replaced by lightweight mocks at the test level anyway, so these stubs are
never called during test execution.
"""
import sys
import types
from unittest.mock import MagicMock


def _make_stub(name: str) -> types.ModuleType:
    """Return a minimal stub module with the given name."""
    mod = types.ModuleType(name)
    sys.modules[name] = mod
    return mod


# ── insightface ────────────────────────────────────────────────────────────────
_insightface = _make_stub("insightface")
_insightface_app = _make_stub("insightface.app")
_insightface_app.FaceAnalysis = MagicMock()

# ── onnxruntime ────────────────────────────────────────────────────────────────
_make_stub("onnxruntime")

# ── mediapipe (used by quality service / kiosk scanner) ───────────────────────
_make_stub("mediapipe")
