from typing import Any

from pymilvus import DataType, MilvusClient


class MilvusV2Repository:
    COLLECTION_NAME = "face_embeddings_v2"
    EMBEDDING_DIMENSION = 512

    def __init__(
        self,
        client: MilvusClient,
        collection_name: str | None = None,
    ) -> None:
        self._client = client
        self._collection_name = collection_name or self.COLLECTION_NAME

    @property
    def collection_name(self) -> str:
        return self._collection_name

    def create_collection(self) -> None:
        if self._client.has_collection(self._collection_name):
            return

        schema = self._client.create_schema(
            auto_id=False,
            enable_dynamic_field=False,
        )

        schema.add_field(
            field_name="vector_id",
            datatype=DataType.INT64,
            is_primary=True,
        )

        schema.add_field(
            field_name="employee_id",
            datatype=DataType.VARCHAR,
            max_length=50,
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

        schema.add_field(
            field_name="embedding_version",
            datatype=DataType.VARCHAR,
            max_length=100,
        )

        schema.add_field(
            field_name="created_at",
            datatype=DataType.INT64,
        )

        index_params = self._client.prepare_index_params()

        index_params.add_index(
            field_name="embedding",
            index_type="AUTOINDEX",
            metric_type="COSINE",
        )

        self._client.create_collection(
            collection_name=self._collection_name,
            schema=schema,
            index_params=index_params,
        )

    def insert_embedding(
        self,
        *,
        vector_id: int,
        employee_id: str,
        embedding: list[float],
        model_name: str,
        model_version: str,
        embedding_version: str,
        created_at: int,
    ) -> None:
        if len(embedding) != self.EMBEDDING_DIMENSION:
            raise ValueError(
                f"Expected {self.EMBEDDING_DIMENSION} dimensions, "
                f"got {len(embedding)}"
            )

        self._client.insert(
            collection_name=self._collection_name,
            data=[
                {
                    "vector_id": vector_id,
                    "employee_id": employee_id,
                    "embedding": embedding,
                    "model_name": model_name,
                    "model_version": model_version,
                    "embedding_version": embedding_version,
                    "created_at": created_at,
                }
            ],
        )

    # def search_embedding(
    #     self,
    #     embedding: list[float],
    #     *,
    #     limit: int = 5,
    # ) -> list[dict[str, Any]]:
    #     if len(embedding) != self.EMBEDDING_DIMENSION:
    #         raise ValueError(
    #             f"Expected {self.EMBEDDING_DIMENSION} dimensions, "
    #             f"got {len(embedding)}"
    #         )

    #     results = self._client.search(
    #         collection_name=self._collection_name,
    #         data=[embedding],
    #         anns_field="embedding",
    #         search_params={
    #             "metric_type": "COSINE",
    #         },
    #         limit=limit,
    #         output_fields=[
    #             "employee_id",
    #             "model_name",
    #             "model_version",
    #             "embedding_version",
    #             "created_at",
    #         ],
    #     )

    #     return [
    #         {
    #             "vector_id": result.id,
    #             "distance": result.distance,
    #             **result.entity,
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
            collection_name=self._collection_name,
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

    def delete_embeddings(
        self,
        vector_ids: list[int],
    ) -> None:
        if not vector_ids:
            return

        self._client.delete(
            collection_name=self._collection_name,
            filter=f"vector_id in {vector_ids}",
        )

    def delete_employee_embeddings(
        self,
        employee_id: str,
    ) -> None:
        self._client.delete(
            collection_name=self._collection_name,
            filter=f'employee_id == "{employee_id}"',
        )

    def delete_vectors(
        self,
        vector_ids: list[int],
    ) -> None:
        if not vector_ids:
            return

        self._client.delete(
            collection_name=self._collection_name,
            filter=f"vector_id in {vector_ids}",
        )

    def get_employee_embeddings(
        self,
        employee_id: str,
    ) -> list[dict[str, Any]]:
        return self._client.query(
            collection_name=self._collection_name,
            filter=f'employee_id == "{employee_id}"',
            output_fields=["vector_id"],
        )