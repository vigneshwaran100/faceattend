from typing import Any, Literal

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.models.scanner_type import ScannerType


class Settings(BaseSettings):
    app_name: str = "Face Recognition System"

    environment: Literal[
        "development",
        "testing",
        "production",
    ] = "development"

    log_level: Literal[
        "DEBUG",
        "INFO",
        "WARNING",
        "ERROR",
        "CRITICAL",
    ] = "INFO"

    camera_index: int = 0
    face_similarity_threshold: float = 0.60

    scanner_mode: ScannerType = ScannerType.CHECK_IN

    end_of_day_hour: int = 22
    end_of_day_minute: int = 0

    jwt_secret: str = "default-insecure-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 60

    database_url: str
    milvus_uri: str
    milvus_collection_name: str = "face_embeddings_v2"

    cors_origins: list[str] = []

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @field_validator("scanner_mode", mode="before")
    @classmethod
    def validate_scanner_mode(cls, value: Any) -> ScannerType:
        if isinstance(value, ScannerType):
            return value

        if isinstance(value, str):
            normalized = value.strip().lower()
            try:
                return ScannerType(normalized)
            except ValueError:
                valid_modes = [mode.value for mode in ScannerType]
                raise ValueError(
                    f"Invalid scanner_mode '{value}'. "
                    f"Must be one of: {valid_modes}"
                )

        raise ValueError(
            "scanner_mode must be a valid string or ScannerType"
        )

    @field_validator("camera_index")
    @classmethod
    def validate_camera_index(cls, value: int) -> int:
        if value < 0:
            raise ValueError(
                "camera_index must be greater than or equal to 0"
            )

        return value

    @field_validator("face_similarity_threshold")
    @classmethod
    def validate_face_similarity_threshold(
        cls,
        value: float,
    ) -> float:
        if not 0 < value <= 1:
            raise ValueError(
                "face_similarity_threshold must be greater than 0 "
                "and less than or equal to 1"
            )

        return value

    @field_validator("end_of_day_hour")
    @classmethod
    def validate_end_of_day_hour(cls, value: int) -> int:
        if not 0 <= value <= 23:
            raise ValueError("end_of_day_hour must be between 0 and 23")
        return value

    @field_validator("end_of_day_minute")
    @classmethod
    def validate_end_of_day_minute(cls, value: int) -> int:
        if not 0 <= value <= 59:
            raise ValueError("end_of_day_minute must be between 0 and 59")
        return value

    @field_validator("jwt_secret", "jwt_algorithm")
    @classmethod
    def validate_jwt_strings(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("JWT configuration value must not be empty")
        return value.strip()

    @field_validator("jwt_access_token_expire_minutes")
    @classmethod
    def validate_jwt_expire_minutes(cls, value: int) -> int:
        if value <= 0:
            raise ValueError(
                "jwt_access_token_expire_minutes must be greater than 0"
            )
        return value

    @field_validator("database_url", "milvus_uri")
    @classmethod
    def validate_required_urls(cls, value: str) -> str:
        if not value.strip():
            raise ValueError(
                "configuration value must not be empty"
            )

        return value.strip()

    @field_validator("cors_origins", mode="before")
    @classmethod
    def validate_cors_origins(cls, value: Any) -> list[str]:
        if value is None:
            return []
        if isinstance(value, str):
            trimmed = value.strip()
            if not trimmed:
                return []
            if trimmed.startswith("[") and trimmed.endswith("]"):
                import json

                try:
                    parsed = json.loads(trimmed)
                    return [str(item).strip() for item in parsed if str(item).strip()]
                except Exception:
                    pass
            return [origin.strip() for origin in trimmed.split(",") if origin.strip()]
        if isinstance(value, (list, tuple, set)):
            return [str(origin).strip() for origin in value if str(origin).strip()]
        return []

    @model_validator(mode="after")
    def validate_environment_settings(self) -> "Settings":
        if not self.cors_origins:
            if self.environment == "development":
                self.cors_origins = [
                    "http://localhost:3000",
                    "http://localhost:5173",
                    "http://127.0.0.1:3000",
                    "http://127.0.0.1:5173",
                ]
            elif self.environment == "testing":
                self.cors_origins = []

        if self.environment == "production":
            insecure_defaults = {
                "default-insecure-secret-key-change-in-production",
                "secret",
                "changeme",
                "password",
            }
            if self.jwt_secret in insecure_defaults or len(self.jwt_secret) < 32:
                raise ValueError(
                    "In production environment, jwt_secret must be a strong secret (at least 32 characters) and not use default placeholders."
                )

            normalized_db = self.database_url.lower()
            if "sqlite" in normalized_db or ":memory:" in normalized_db:
                raise ValueError(
                    "In production environment, database_url cannot use SQLite or in-memory databases."
                )
            if "attendance_password" in self.database_url or "user:password@" in self.database_url:
                raise ValueError(
                    "In production environment, database_url must not use default or placeholder credentials."
                )

            if not self.cors_origins:
                raise ValueError(
                    "In production environment, cors_origins must be explicitly configured with allowed origins."
                )
            if "*" in self.cors_origins:
                raise ValueError(
                    "In production environment, cors_origins must not contain wildcard '*'."
                )
        return self


settings = Settings()