from sqlalchemy import text

from app.infrastructure.database import create_database_engine


def main() -> None:
    engine = create_database_engine()

    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            print(f"PostgreSQL connection successful: {result.scalar()}")
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()