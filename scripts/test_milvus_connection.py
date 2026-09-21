from app.core.config import settings
from app.infrastructure.milvus_client import MilvusConnection


def main() -> None:
    connection = MilvusConnection(uri=settings.milvus_uri)

    try:
        collections = connection.client.list_collections()

        print("Milvus connection successful!")
        print(f"Collections: {collections}")

    finally:
        connection.close()


if __name__ == "__main__":
    main()