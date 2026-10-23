import os
import asyncio

import urllib3
from dotenv import load_dotenv
from pinecone import Pinecone, ServerlessSpec
from pinecone.exceptions import PineconeException, UnauthorizedException

load_dotenv()

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
INDEX_NAME = os.getenv("INDEX_NAME", "module4-index")
NAMESPACE = os.getenv("NAMESPACE", "dev-env")
REQUIRED_METADATA_FIELDS = ("topic", "priority")


def validate_vector_metadata(vectors: list[tuple]) -> None:
    """Require every vector to include the metadata fields used at query time."""
    for vector_id, _values, metadata in vectors:
        if not isinstance(metadata, dict):
            raise ValueError(f"Vector '{vector_id}' metadata must be a dict.")
        missing = [
            field
            for field in REQUIRED_METADATA_FIELDS
            if metadata.get(field) in (None, "")
        ]
        if missing:
            fields = ", ".join(missing)
            raise ValueError(
                f"Vector '{vector_id}' is missing required metadata fields: {fields}."
            )


def init_pinecone_client(api_key: str) -> Pinecone:
    """Create the client and confirm the API key can reach Pinecone."""
    if not api_key:
        raise RuntimeError("Set PINECONE_API_KEY in the environment or in the .env file.")

    try:
        client = Pinecone(api_key=api_key)
        client.list_indexes()
    except UnauthorizedException as exc:
        raise RuntimeError(
            "Pinecone rejected the API key. Check PINECONE_API_KEY."
        ) from exc
    except (PineconeException, urllib3.exceptions.HTTPError, OSError) as exc:
        raise RuntimeError(
            "Could not connect to Pinecone. Check your network and credentials."
        ) from exc

    return client


async def setup_vector_infrastructure(index_name: str, dimension: int):
    """
    Set up Pinecone Serverless infrastructure and load an initial batch of vectors.
    """
    # 1. Initialize the Pinecone client
    pc = init_pinecone_client(PINECONE_API_KEY)

    # 2. Create the index if it does not exist. create_index waits until it is ready.
    if index_name not in pc.list_indexes().names():
        pc.create_index(
            name=index_name,
            dimension=dimension,
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region="us-east-1"),
        )

    # 3. Connect to the index
    index = pc.Index(index_name)

    # 4. Test upsert into the namespace
    vectors = [
        ("vec1", [0.1] * dimension, {"topic": "infrastructure", "priority": "high"}),
        ("vec2", [0.2] * dimension, {"topic": "embeddings", "priority": "medium"}),
        ("vec3", [0.3] * dimension, {"topic": "namespaces", "priority": "low"}),
    ]
    validate_vector_metadata(vectors)
    index.upsert(vectors=vectors, namespace=NAMESPACE)

    # 5. Stats can take a few seconds to reflect the upsert
    stats = index.describe_index_stats()
    for _ in range(6):
        namespace_stats = (stats.namespaces or {}).get(NAMESPACE)
        vector_count = getattr(namespace_stats, "vector_count", 0) or 0
        if vector_count:
            break
        await asyncio.sleep(2)
        stats = index.describe_index_stats()

    print(stats)
    return stats


if __name__ == "__main__":
    # Example with dimension 1536 (OpenAI)
    asyncio.run(setup_vector_infrastructure(INDEX_NAME, 1536))
