from typing import List, Union

from pydantic import BaseModel, Field
from langchain_core.tools import tool


class SearchInput(BaseModel):
    """Validated arguments for a knowledge-base search."""

    query: str = Field(
        ...,
        description=(
            "Natural-language question or keywords to look up in the "
            "knowledge base, such as a policy name or a procedure."
        ),
    )
    limit: int = Field(
        default=3,
        ge=1,
        le=10,
        description=(
            "Maximum number of matching documents to return. "
            "Must be an integer between 1 and 10."
        ),
    )


# Stand-in for a vector database. Returns canned hits so the tool
# can be exercised without an embedding model or a live index.
class MockVectorDB:
    async def similarity_search(self, query: str, k: int) -> List[str]:
        return [f"Result for {query}"]


db = MockVectorDB()


@tool(args_schema=SearchInput)
async def search_knowledge_base(query: str, limit: int = 3) -> Union[List[str], str]:
    """Search the company knowledge base for passages relevant to a question.

    Use this tool when the answer should come from internal documents
    (policies, procedures, handbooks) instead of general knowledge.
    Do not use it for chit-chat, math, or questions unrelated to those documents.

    Returns a list of matching document snippets, at most `limit` items.
    If the search fails, returns an error message so the caller can explain
    the failure or try another approach.
    """
    try:
        return await db.similarity_search(query, k=limit)
    except Exception as exc:
        return f"Knowledge base search failed: {exc}"


if __name__ == "__main__":
    import asyncio

    print(search_knowledge_base.name, search_knowledge_base.args)
    print(
        asyncio.run(
            search_knowledge_base.ainvoke(
                {"query": "vacation policies", "limit": 2}
            )
        )
    )
