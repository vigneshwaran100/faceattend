from unittest.mock import patch

from fastapi.testclient import TestClient
import pytest
from pydantic import ValidationError

from app.api.main import app
from app.core.config import Settings
from app.infrastructure.milvus_client import (
    MilvusConnection,
    MilvusConnectionError,
    sanitize_uri,
)


# ==============================================================================
# 1. Environment & Production Settings Hardening Tests
# ==============================================================================


def test_production_rejects_sqlite_database() -> None:
    with pytest.raises(ValidationError) as exc_info:
        Settings(
            database_url="sqlite:///test.db",
            milvus_uri="http://localhost:19530",
            environment="production",
            jwt_secret="a" * 32,
            cors_origins=["https://attendance.example.com"],
        )
    assert "cannot use sqlite" in str(exc_info.value).lower()


def test_production_rejects_default_dev_credentials() -> None:
    with pytest.raises(ValidationError) as exc_info:
        Settings(
            database_url="postgresql+psycopg://attendance_user:attendance_password@db:5432/smart_attendance",
            milvus_uri="http://localhost:19530",
            environment="production",
            jwt_secret="a" * 32,
            cors_origins=["https://attendance.example.com"],
        )
    assert "default or placeholder credentials" in str(exc_info.value).lower()


def test_production_requires_explicit_cors_origins() -> None:
    with pytest.raises(ValidationError) as exc_info:
        Settings(
            database_url="postgresql+psycopg://prod_user:StrongPassword987!@db:5432/attendance_prod",
            milvus_uri="http://milvus:19530",
            environment="production",
            jwt_secret="a" * 32,
            cors_origins=[],
        )
    assert "cors_origins must be explicitly configured" in str(exc_info.value).lower()


def test_production_rejects_wildcard_cors() -> None:
    with pytest.raises(ValidationError) as exc_info:
        Settings(
            database_url="postgresql+psycopg://prod_user:StrongPassword987!@db:5432/attendance_prod",
            milvus_uri="http://milvus:19530",
            environment="production",
            jwt_secret="a" * 32,
            cors_origins=["*"],
        )
    assert "wildcard '*'" in str(exc_info.value).lower()


def test_production_accepts_valid_hardened_settings() -> None:
    settings = Settings(
        database_url="postgresql+psycopg://prod_user:StrongPassword987!@db:5432/attendance_prod",
        milvus_uri="http://milvus:19530",
        environment="production",
        jwt_secret="secure_random_jwt_secret_key_prod_2026",
        cors_origins=["https://attendance.example.com"],
    )
    assert settings.environment == "production"
    assert settings.cors_origins == ["https://attendance.example.com"]
    assert settings.milvus_collection_name == "face_embeddings_v2"


def test_development_cors_defaults_to_localhost() -> None:
    settings = Settings(
        database_url="postgresql+psycopg://user:pass@localhost:5432/devdb",
        milvus_uri="http://localhost:19530",
        environment="development",
    )
    assert "http://localhost:3000" in settings.cors_origins
    assert "http://localhost:5173" in settings.cors_origins


def test_cors_origins_parses_comma_separated_and_json_strings() -> None:
    settings1 = Settings(
        database_url="postgresql+psycopg://user:pass@localhost:5432/devdb",
        milvus_uri="http://localhost:19530",
        cors_origins="https://app1.example.com, https://app2.example.com",
    )
    assert settings1.cors_origins == [
        "https://app1.example.com",
        "https://app2.example.com",
    ]

    settings2 = Settings(
        database_url="postgresql+psycopg://user:pass@localhost:5432/devdb",
        milvus_uri="http://localhost:19530",
        cors_origins='["https://app3.example.com", "https://app4.example.com"]',
    )
    assert settings2.cors_origins == [
        "https://app3.example.com",
        "https://app4.example.com",
    ]


# ==============================================================================
# 2. Secret Masking & Logging Hardening Tests
# ==============================================================================


def test_sanitize_uri_masks_passwords() -> None:
    plain_uri = "http://milvus_user:super_secret_pw@milvus-cluster:19530"
    sanitized = sanitize_uri(plain_uri)

    assert "super_secret_pw" not in sanitized
    assert sanitized == "http://milvus_user:***@milvus-cluster:19530"


def test_sanitize_uri_preserves_unauthenticated_uris() -> None:
    plain_uri = "http://localhost:19530"
    assert sanitize_uri(plain_uri) == plain_uri


def test_milvus_connection_error_does_not_leak_credentials() -> None:
    secret_pw = "UltraSecretPassword99"
    sensitive_uri = f"http://admin:{secret_pw}@127.0.0.1:1"

    with patch("app.infrastructure.milvus_client.MilvusClient", side_effect=Exception("Connection refused")):
        with pytest.raises(MilvusConnectionError) as exc_info:
            MilvusConnection(uri=sensitive_uri)

        error_message = str(exc_info.value)
        assert secret_pw not in error_message
        assert "admin:***@127.0.0.1:1" in error_message


# ==============================================================================
# 3. Liveness and Readiness Probe Tests
# ==============================================================================


def test_liveness_probe_returns_healthy() -> None:
    with TestClient(app) as client:
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}


def test_readiness_probe_healthy_when_all_up() -> None:
    with patch("app.api.routers.health._check_database", return_value={"status": "healthy", "critical": True}):
        with patch("app.api.routers.health._check_milvus", return_value={"status": "healthy", "critical": False}):
            with TestClient(app) as client:
                response = client.get("/ready")
                assert response.status_code == 200
                data = response.json()
                assert data["status"] == "ready"
                assert data["ready"] is True
                assert data["dependencies"]["database"]["status"] == "healthy"
                assert data["dependencies"]["milvus"]["status"] == "healthy"


def test_readiness_probe_degraded_when_milvus_down() -> None:
    """HTTP 200 degraded status must not be interpreted as Milvus fully operational."""
    with patch("app.api.routers.health._check_database", return_value={"status": "healthy", "critical": True}):
        with patch(
            "app.api.routers.health._check_milvus",
            return_value={
                "status": "unavailable",
                "critical": False,
                "message": "Face enrollment non-operational; core auth & attendance operational",
            },
        ):
            with TestClient(app) as client:
                response = client.get("/ready")
                assert response.status_code == 200
                data = response.json()
                assert data["status"] == "degraded"
                assert data["ready"] is True
                assert data["dependencies"]["database"]["status"] == "healthy"
                # Crucial requirement: milvus status is explicitly unavailable
                assert data["dependencies"]["milvus"]["status"] == "unavailable"
                assert "non-operational" in data["dependencies"]["milvus"]["message"].lower()


def test_readiness_probe_not_ready_when_database_down() -> None:
    with patch("app.api.routers.health._check_database", return_value={"status": "unavailable", "critical": True}):
        with patch("app.api.routers.health._check_milvus", return_value={"status": "healthy", "critical": False}):
            with TestClient(app) as client:
                response = client.get("/ready")
                assert response.status_code == 503
                data = response.json()
                assert data["status"] == "not_ready"
                assert data["ready"] is False
                assert data["dependencies"]["database"]["status"] == "unavailable"
