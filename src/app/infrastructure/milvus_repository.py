from pymilvus import DataType, MilvusClient
from typing import Any

class MilvusRepository:
    COLLECTION_NAME = "face_embeddings"
    EMBEDDING_DIMENSION = 512

    def __init__(self, client: MilvusClient) -> None:
        self._client = client

    def create_collection(self) -> None:
        if self._client.has_collection(self.COLLECTION_NAME):
            return

        schema = self._client.create_schema(
            auto_id=False,
            enable_dynamic_field=False,
        )

        schema.add_field(
            field_name="id",
            datatype=DataType.INT64,
            is_primary=True,
        )

        schema.add_field(
            field_name="person_id",
            datatype=DataType.VARCHAR,
            max_length=100,
        )

        schema.add_field(
            field_name="person_name",
            datatype=DataType.VARCHAR,
            max_length=200,
        )

        schema.add_field(
            field_name="embedding",
            datatype=DataType.FLOAT_VECTOR,
            dim=self.EMBEDDING_DIMENSION,
        )

        schema.add_field(
            field_name="model_name",
            datatype=DataType.VARCHAR,
            max_length=100,
        )

        schema.add_field(
            field_name="model_version",
            datatype=DataType.VARCHAR,
            max_length=100,
        )

        index_params = self._client.prepare_index_params()

        index_params.add_index(
            field_name="embedding",
            index_type="AUTOINDEX",
            metric_type="COSINE",
        )

        self._client.create_collection(
            collection_name=self.COLLECTION_NAME,
            schema=schema,
            index_params=index_params,
        )
    

    def insert_embedding(
        self,
        *,
        record_id: int,
        person_id: str,
        person_name: str,
        embedding: list[float],
        model_name: str,
        model_version: str,
    ) -> None:
        if not isinstance(embedding, list):
            raise TypeError(
                f"Embedding must be a list, got {type(embedding).__name__}"
            )

        if len(embedding) != self.EMBEDDING_DIMENSION:
            raise ValueError(
                f"Expected {self.EMBEDDING_DIMENSION} dimensions, "
                f"got {len(embedding)}"
            )

        data = {
            "id": record_id,
            "person_id": person_id,
            "person_name": person_name,
            "embedding": embedding,
            "model_name": model_name,
            "model_version": model_version,
        }

        self._client.insert(
            collection_name=self.COLLECTION_NAME,
            data=[data],
        )

    def list_records(self, limit: int = 20) -> list[dict]:
        return self._client.query(
            collection_name=self.COLLECTION_NAME,
            filter="",
            output_fields=[
                "id",
                "person_id",
                "person_name",
                "model_name",
                "model_version",
            ],
            limit=limit,
        )

    # def search_embedding(
    #     self,
    #     embedding: list[float],
    #     *,
    #     limit: int = 5,
    # ) -> list[dict[str, Any]]:
    #     if not isinstance(embedding, list):
    #         raise TypeError(
    #             f"Embedding must be a list, "
    #             f"got {type(embedding).__name__}"
    #         )

    #     if len(embedding) != self.EMBEDDING_DIMENSION:
    #         raise ValueError(
    #             f"Expected {self.EMBEDDING_DIMENSION} dimensions, "
    #             f"got {len(embedding)}"
    #         )

    #     results = self._client.search(
    #         collection_name=self.COLLECTION_NAME,
    #         data=[embedding],
    #         anns_field="embedding",
    #         search_params={
    #             "metric_type": "COSINE",
    #         },
    #         limit=limit,
    #         output_fields=[
    #             "person_id",
    #             "person_name",
    #             "model_name",
    #             "model_version",
    #         ],
    #     )

    #     return [
    #         {
    #             "id": result["id"],
    #             "distance": result["distance"],
    #             **result["entity"],
    #         }
    #         for result in results[0]
    #     ]
    def search_embedding(
        self,
        embedding: list[float],
        *,
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        if len(embedding) != self.EMBEDDING_DIMENSION:
            raise ValueError(
                f"Expected {self.EMBEDDING_DIMENSION} dimensions, "
                f"got {len(embedding)}"
            )

        results = self._client.search(
            collection_name=self.COLLECTION_NAME,
            data=[embedding],
            anns_field="embedding",
            search_params={
                "metric_type": "COSINE",
            },
            limit=limit,
            output_fields=[
                "employee_id",
                "model_name",
                "model_version",
                "embedding_version",
                "created_at",
            ],
        )

        return [
            {
                "vector_id": hit["vector_id"],
                "distance": hit["distance"],
                "employee_id": hit["entity"]["employee_id"],
                "model_name": hit["entity"]["model_name"],
                "model_version": hit["entity"]["model_version"],
                "embedding_version": hit["entity"]["embedding_version"],
                "created_at": hit["entity"]["created_at"],
            }
            for hit in results[0]
        ]