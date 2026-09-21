from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

from app.core.config import settings


def create_database_engine() -> Engine:
    return create_engine(
        settings.database_url,
        pool_pre_ping=True,
    )