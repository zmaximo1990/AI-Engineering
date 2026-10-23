import asyncio
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from dotenv import load_dotenv

from samples import SAMPLE_DOCUMENTS

load_dotenv(Path(__file__).resolve().with_name(".env"))

DOCUMENT_FIELDS = ("text", "category", "author")


def load_embedding_dimension() -> int:
    """Read EMBEDDING_DIMENSION from the environment. Defaults to 8."""
    raw = os.getenv("EMBEDDING_DIMENSION", "8").strip()
    if not raw.isdigit() or int(raw) < 1:
        raise ValueError(
            f"EMBEDDING_DIMENSION must be a positive integer, got {raw!r}."
        )
    return int(raw)


EMBEDDING_DIMENSION = load_embedding_dimension()


class MockPineconeIndex:
    """Stand-in for a Pinecone index so ingestion can be tested without an account."""

    async def upsert(self, vectors: List[Dict]):
        """Simulate a batch insert and report how many vectors were sent."""
        print(len(vectors))
        return {"upserted_count": len(vectors)}

    async def query(self, vector: List[float], top_k: int, filter: Dict = None):
        """Simulate a filtered similarity query. Matches stay empty on purpose."""
        print(filter)
        return {"matches": []}


class IngestionPipeline:
    def __init__(self, index: MockPineconeIndex, embedding_dimension: int):
        if isinstance(embedding_dimension, bool) or not isinstance(embedding_dimension, int):
            raise ValueError("embedding_dimension must be a positive integer.")
        if embedding_dimension < 1:
            raise ValueError("embedding_dimension must be a positive integer.")
        self.index = index
        self.embedding_dimension = embedding_dimension

    def validate_document(self, document: Any, index: int) -> Dict[str, str]:
        """Check that a document has the required string fields before ingestion."""
        if not isinstance(document, dict):
            raise ValueError(f"Document at index {index} must be a dict.")

        fields: Dict[str, str] = {}
        for name in DOCUMENT_FIELDS:
            if name not in document:
                raise ValueError(
                    f"Document at index {index} is missing required field '{name}'."
                )
            value = document[name]
            if not isinstance(value, str):
                raise ValueError(
                    f"Document at index {index} field '{name}' must be a string."
                )
            fields[name] = value
        return fields

    def create_metadata(self, doc_text: str, category: str, author: str) -> Dict[str, Any]:
        """
        Build a strict metadata record so every document uses the same fields.

        Fields: category, author, ingested_at (ISO-8601), and char_count.
        """
        for label, value in (
            ("doc_text", doc_text),
            ("category", category),
            ("author", author),
        ):
            if not isinstance(value, str):
                raise ValueError(f"{label} must be a string.")

        return {
            "category": category,
            "author": author,
            "ingested_at": datetime.now().isoformat(),
            "char_count": len(doc_text),
        }

    async def process_and_upsert_batches(
        self, documents: List[Dict], batch_size: int = 100
    ) -> int:
        """
        Split documents into batches, attach metadata, and upsert each batch once.

        A failed upsert is reported and skipped so later batches still run.
        Returns the number of documents processed successfully.
        """
        if not isinstance(documents, list):
            raise ValueError("documents must be a list.")
        if isinstance(batch_size, bool) or not isinstance(batch_size, int) or batch_size < 1:
            raise ValueError("batch_size must be a positive integer.")

        total_processed = 0
        for start in range(0, len(documents), batch_size):
            batch = documents[start : start + batch_size]
            validated = [
                self.validate_document(doc, start + offset)
                for offset, doc in enumerate(batch)
            ]
            vectors = [
                {
                    "id": str(uuid.uuid4()),
                    "values": [0.1] * self.embedding_dimension,
                    "metadata": self.create_metadata(
                        fields["text"], fields["category"], fields["author"]
                    ),
                }
                for fields in validated
            ]
            try:
                await self.index.upsert(vectors)
            except Exception as exc:
                print(
                    "Upsert failed for batch starting at document "
                    f"{start} ({len(vectors)} vectors): {type(exc).__name__}: {exc}"
                )
                continue
            total_processed += len(vectors)
        return total_processed

    async def search_by_category(self, query_vector: List[float], category: str):
        """Query similar vectors restricted to a single category."""
        return await self.index.query(
            vector=query_vector,
            top_k=5,
            filter={"category": {"$eq": category}},
        )


async def main():
    index = MockPineconeIndex()
    pipeline = IngestionPipeline(index, EMBEDDING_DIMENSION)

    total_processed = await pipeline.process_and_upsert_batches(
        SAMPLE_DOCUMENTS, batch_size=2
    )
    print(total_processed)

    query_vector = [0.1] * pipeline.embedding_dimension
    results = await pipeline.search_by_category(query_vector, "legal")
    print(results)


if __name__ == "__main__":
    asyncio.run(main())
