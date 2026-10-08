import asyncio
import functools
import inspect
import os
from collections.abc import AsyncIterator, Awaitable, Callable
from typing import cast

"""
One semaphore per provider. A 429 is enforced by that provider, so OpenAI
traffic must not consume Anthropic or Gemini permits. SEMAPHORE_LIMIT is the
cap for each provider, not a shared pool.
"""
_limit = int(os.environ.get("SEMAPHORE_LIMIT", 10))
openai_sem = asyncio.Semaphore(_limit)
anthropic_sem = asyncio.Semaphore(_limit)
gemini_sem = asyncio.Semaphore(_limit)

"""
Decorator to limit the number of concurrent calls to the APIs.
"""
def limit_concurrency[**P, R](
    sem: asyncio.Semaphore | int,
) -> Callable[
    [Callable[P, Awaitable[R] | AsyncIterator[R]]],
    Callable[P, Awaitable[R] | AsyncIterator[R]],
]:
    semaphore = asyncio.Semaphore(sem) if isinstance(sem, int) else sem

    def decorator(
        fn: Callable[P, Awaitable[R] | AsyncIterator[R]],
    ) -> Callable[P, Awaitable[R] | AsyncIterator[R]]:
        if inspect.isasyncgenfunction(fn):
            agen = cast(Callable[P, AsyncIterator[R]], fn)

            @functools.wraps(fn)
            async def agen_wrapper(*args: P.args, **kwargs: P.kwargs) -> AsyncIterator[R]:
                async with semaphore:
                    async for item in agen(*args, **kwargs):
                        yield item

            return agen_wrapper

        coro = cast(Callable[P, Awaitable[R]], fn)

        @functools.wraps(fn)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            async with semaphore:
                return await coro(*args, **kwargs)

        return wrapper

    return decorator
