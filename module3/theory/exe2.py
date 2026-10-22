"""
Spec:

Objetivo: encapsular las operaciones CRUD de ChromaDB en una clase robusta.

Manos a la obra:
Inicializá un PersistentClient con una ruta de disco y una colección.
Implementá upsert_documents y semantic_search usando collection.query().
Resultado: tu VectorMemoryManager listo para poblar y consultar tu base vectorial.
"""

import os
from pathlib import Path
from typing import Any

import chromadb
from chromadb.api.models import Collection as ChromaDBCollection
from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_core.embeddings import Embeddings
from langchain_huggingface import HuggingFaceEmbeddings

load_dotenv(Path(__file__).resolve().with_name(".env"))

COLLECTION_NAME = os.getenv("collection_name", "knowledge_base")
DB_NAME = os.getenv("db_name", "chroma_db")
MODEL_NAME = os.getenv("model_name", "sentence-transformers/all-MiniLM-L6-v2")

# class ChromaOnnxEmbeddings(Embeddings):
#     """Chroma's built-in ONNX MiniLM, exposed as a LangChain embedding model."""

#     def __init__(self) -> None:
#         self._model = ONNXMiniLM_L6_V2()

#     def embed_documents(self, texts: list[str]) -> list[list[float]]:
#         return [vector.tolist() for vector in self._model(texts)]

#     def embed_query(self, text: str) -> list[float]:
#         return self.embed_documents([text])[0]

embeddings_model: Embeddings = HuggingFaceEmbeddings(model_name=MODEL_NAME)

class VectorMemoryManager:
    def __init__(
        self,
        db_name: str = DB_NAME,
        collection_name: str = COLLECTION_NAME,
    ):
        # Embedded Chroma: data lives on disk, no server.
        persist_path = Path(db_name)
        if not persist_path.is_absolute():
            persist_path = Path(__file__).resolve().parent / persist_path
        self.client = chromadb.PersistentClient(path=str(persist_path))
        self.store = Chroma(
            client=self.client,
            collection_name=collection_name,
            embedding_function=embeddings_model,
        )
        self.collection: ChromaDBCollection = self.store._collection

    def upsert_documents(
        self,
        ids: list[str],
        documents: list[str],
        metadatas: list[dict[str, Any]],
    ) -> None:
        """Insert documents, or replace them when the id already exists."""
        self.store.add_texts(texts=documents, metadatas=metadatas, ids=ids)

    def semantic_search(
        self,
        query_text: str,
        n_results: int = 3,
        where: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Return the nearest documents. Lower distance means a closer match."""
        pairs = self.store.similarity_search_with_score(
            query_text,
            k=n_results,
            filter=where,
        )
        return [
            {
                "document": document.page_content,
                "metadata": document.metadata,
                "distance": float(distance),
            }
            for document, distance in pairs
        ]

    def delete_by_id(self, ids: list[str]) -> None:
        """Remove documents by id."""
        self.store.delete(ids=ids)


if __name__ == "__main__":
    manager = VectorMemoryManager()
    manager.upsert_documents(
        ["doc1", "doc2", "doc3"],
        [
            "Python 3.12 introduce mejoras en asyncio y tipos.",
            "Las bases de datos vectoriales son clave para la memoria de largo plazo en IA.",
            "FastAPI permite crear APIs asíncronas en Python.",
        ],
        [{"source": "news"}, {"source": "tech_blog"}, {"source": "tech_blog"}],
    )
    print("Semantic search results:")
    print("-" * 50)
    print(manager.semantic_search("mejoras en python"))
    print("-" * 50)
    print(manager.semantic_search("memoria de IA", where={"source": "tech_blog"}))
    print("-" * 50)
    manager.delete_by_id(["doc2"])
    print("Number of documents in the collection:", manager.collection.count())
