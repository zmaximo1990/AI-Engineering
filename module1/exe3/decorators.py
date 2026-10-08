import asyncio
import functools
import inspect
import os
from collections.abc import AsyncIterator, Awaitable, Callable
from typing import cast

"""
We are using a semaphore to limit the number of concurrent calls to the APIs.
"""
sem = asyncio.Semaphore(int(os.environ.get("SEMAPHORE_LIMIT", 10)))

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
