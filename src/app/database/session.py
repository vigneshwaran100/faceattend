from collections.abc import Generator

from sqlalchemy.orm import Session, sessionmaker

from app.infrastructure.database import create_database_engine


engine = create_database_engine()

SessionFactory = sessionmaker(
    bind=engine,
    autoflush=False,
    expire_on_commit=False,
)


def get_session() -> Generator[Session, None, None]:
    with SessionFactory() as session:
        yield session