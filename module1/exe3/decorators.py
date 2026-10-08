import asyncio
import functools
import inspect
import logging
import os
from collections.abc import AsyncIterator, Awaitable, Callable
from typing import cast

logger = logging.getLogger(__name__)

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


"""
Abort a call that exceeds TIMEOUT seconds (default 60). TimeoutError is logged
and swallowed so one slow provider does not abort the rest of the run.
"""
_raw_timeout = os.environ.get("TIMEOUT", "").strip()
_timeout_seconds = int(_raw_timeout) if _raw_timeout else 60


def timeout[**P, R](
    fn: Callable[P, Awaitable[R] | AsyncIterator[R]],
) -> Callable[P, Awaitable[R] | AsyncIterator[R]]:
    if inspect.isasyncgenfunction(fn):
        agen = cast(Callable[P, AsyncIterator[R]], fn)

        @functools.wraps(fn)
        async def agen_wrapper(*args: P.args, **kwargs: P.kwargs) -> AsyncIterator[R]:
            try:
                async with asyncio.timeout(_timeout_seconds):
                    async for item in agen(*args, **kwargs):
                        yield item
            except TimeoutError:
                # Here we could implement retry logic with backoff + jitter
                logger.error(
                    "%s timed out after %ss", fn.__qualname__, _timeout_seconds
                )
                yield cast(R, f"\n[⚠️ Timeout after {_timeout_seconds}s]")

        return agen_wrapper

    coro = cast(Callable[P, Awaitable[R]], fn)

    @functools.wraps(fn)
    async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        try:
            async with asyncio.timeout(_timeout_seconds):
                return await coro(*args, **kwargs)
        except TimeoutError:
            instance = args[0] if args else None
            error_response = getattr(instance, "_error_response", None)
            if callable(error_response):
                return cast(
                    R,
                    error_response(
                        TimeoutError(
                            f"{fn.__qualname__} timed out after {_timeout_seconds}s"
                        )
                    ),
                )
            return cast(R, None)

    return wrapper
