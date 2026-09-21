import logging
from urllib.parse import urlsplit, urlunsplit
from pymilvus import MilvusClient

logger = logging.getLogger(__name__)


def sanitize_uri(uri: str) -> str:
    """Mask any embedded password in URI before logging or error display."""
    try:
        parsed = urlsplit(uri)
        if parsed.password:
            user = parsed.username or ""
            host = parsed.hostname or ""
            netloc = f"{user}:***@{host}"
            if parsed.port:
                netloc = f"{netloc}:{parsed.port}"
            return urlunsplit((
                parsed.scheme,
                netloc,
                parsed.path,
                parsed.query,
                parsed.fragment,
            ))
        return uri
    except Exception:
        return "[sanitized-uri]"


class MilvusConnectionError(RuntimeError):
    """Raised when the Milvus connection cannot be created."""


class MilvusConnection:
    def __init__(
        self,
        uri: str,
    ) -> None:
        sanitized = sanitize_uri(uri)
        try:
            self._client = MilvusClient(uri=uri)
        except Exception as error:
            logger.error(
                "Failed to connect to Milvus at %s | error=%s",
                sanitized,
                error,
            )
            raise MilvusConnectionError(
                f"Unable to connect to Milvus at {sanitized}"
            ) from error

    @property
    def client(self) -> MilvusClient:
        return self._client

    def close(self) -> None:
        self._client.close()