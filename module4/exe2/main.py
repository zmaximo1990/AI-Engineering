import asyncio
import uuid
from datetime import datetime
from typing import Any, Dict, List

from samples import SAMPLE_DOCUMENTS

EMBEDDING_DIMENSION = 8


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
    def __init__(self, index: MockPineconeIndex):
        self.index = index

    def create_metadata(self, doc_text: str, category: str, author: str) -> Dict[str, Any]:
        """
        Build a strict metadata record so every document uses the same fields.

        Fields: category, author, ingested_at (ISO-8601), and char_count.
        """
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

        Returns the number of documents processed.
        """
        total_processed = 0
        for start in range(0, len(documents), batch_size):
            batch = documents[start : start + batch_size]
            vectors = [
                {
                    "id": str(uuid.uuid4()),
                    "values": [0.1] * EMBEDDING_DIMENSION,
                    "metadata": self.create_metadata(
                        doc["text"], doc["category"], doc["author"]
                    ),
                }
                for doc in batch
            ]
            await self.index.upsert(vectors)
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
    pipeline = IngestionPipeline(index)

    total_processed = await pipeline.process_and_upsert_batches(
        SAMPLE_DOCUMENTS, batch_size=2
    )
    print(total_processed)

    query_vector = [0.1] * EMBEDDING_DIMENSION
    results = await pipeline.search_by_category(query_vector, "legal")
    print(results)


if __name__ == "__main__":
    asyncio.run(main())
