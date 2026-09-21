import pytest
from pydantic import ValidationError

from app.core.config import Settings


def test_valid_settings() -> None:
    settings = Settings(
        database_url="postgresql+psycopg://user:pass@localhost:5432/db",
        milvus_uri="http://localhost:19530",
        camera_index=0,
        face_similarity_threshold=0.60,
        environment="development",
        log_level="INFO",
    )

    assert settings.camera_index == 0
    assert settings.face_similarity_threshold == 0.60
    assert settings.environment == "development"
    assert settings.log_level == "INFO"


def test_rejects_negative_camera_index() -> None:
    with pytest.raises(ValidationError):
        Settings(
            database_url="postgresql+psycopg://user:pass@localhost:5432/db",
            milvus_uri="http://localhost:19530",
            camera_index=-1,
        )


def test_rejects_invalid_similarity_threshold_zero() -> None:
    with pytest.raises(ValidationError):
        Settings(
            database_url="postgresql+psycopg://user:pass@localhost:5432/db",
            milvus_uri="http://localhost:19530",
            face_similarity_threshold=0.0,
        )


def test_rejects_invalid_similarity_threshold_greater_than_one() -> None:
    with pytest.raises(ValidationError):
        Settings(
            database_url="postgresql+psycopg://user:pass@localhost:5432/db",
            milvus_uri="http://localhost:19530",
            face_similarity_threshold=1.5,
        )


def test_rejects_empty_database_url() -> None:
    with pytest.raises(ValidationError):
        Settings(
            database_url="   ",
            milvus_uri="http://localhost:19530",
        )


def test_rejects_empty_milvus_uri() -> None:
    with pytest.raises(ValidationError):
        Settings(
            database_url="postgresql+psycopg://user:pass@localhost:5432/db",
            milvus_uri="   ",
        )


def test_rejects_invalid_environment() -> None:
    with pytest.raises(ValidationError):
        Settings(
            database_url="postgresql+psycopg://user:pass@localhost:5432/db",
            milvus_uri="http://localhost:19530",
            environment="staging",  # type: ignore[arg-type]
        )


def test_rejects_invalid_log_level() -> None:
    with pytest.raises(ValidationError):
        Settings(
            database_url="postgresql+psycopg://user:pass@localhost:5432/db",
            milvus_uri="http://localhost:19530",
            log_level="VERBOSE",  # type: ignore[arg-type]
        )


def test_jwt_settings_valid() -> None:
    settings = Settings(
        database_url="postgresql+psycopg://user:pass@localhost:5432/db",
        milvus_uri="http://localhost:19530",
        jwt_secret="custom-secret-key-123",
        jwt_algorithm="HS256",
        jwt_access_token_expire_minutes=120,
    )
    assert settings.jwt_secret == "custom-secret-key-123"
    assert settings.jwt_algorithm == "HS256"
    assert settings.jwt_access_token_expire_minutes == 120


def test_rejects_empty_jwt_secret() -> None:
    with pytest.raises(ValidationError):
        Settings(
            database_url="postgresql+psycopg://user:pass@localhost:5432/db",
            milvus_uri="http://localhost:19530",
            jwt_secret="   ",
        )


def test_rejects_non_positive_jwt_expire_minutes() -> None:
    with pytest.raises(ValidationError):
        Settings(
            database_url="postgresql+psycopg://user:pass@localhost:5432/db",
            milvus_uri="http://localhost:19530",
            jwt_access_token_expire_minutes=0,
        )


def test_production_rejects_default_placeholder_jwt_secret() -> None:
    with pytest.raises(ValidationError) as exc_info:
        Settings(
            database_url="postgresql+psycopg://user:pass@localhost:5432/db",
            milvus_uri="http://localhost:19530",
            environment="production",
            jwt_secret="default-insecure-secret-key-change-in-production",
        )
    assert "strong secret" in str(exc_info.value).lower()


def test_production_rejects_short_jwt_secret() -> None:
    with pytest.raises(ValidationError) as exc_info:
        Settings(
            database_url="postgresql+psycopg://user:pass@localhost:5432/db",
            milvus_uri="http://localhost:19530",
            environment="production",
            jwt_secret="short-secret-less-than-32-chr",
        )
    assert "at least 32 characters" in str(exc_info.value).lower()


def test_production_accepts_strong_jwt_secret() -> None:
    strong_secret = "a" * 32
    settings = Settings(
        database_url="postgresql+psycopg://user:pass@localhost:5432/db",
        milvus_uri="http://localhost:19530",
        environment="production",
        jwt_secret=strong_secret,
        cors_origins=["https://attendance.example.com"],
    )
    assert settings.jwt_secret == strong_secret


