import asyncio
import random
import logging
import time
import functools
from collections.abc import Awaitable, Callable

# Enable logging
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)

# Constants
SEMAPHORE_LIMIT = 3
MIN_LATENCY = 0.5
MAX_LATENCY = 2.5
TIMEOUT = 10
OPENAI_TASKS_COUNT = 5
ANTHROPIC_TASKS_COUNT = 5
LLAMA_TASKS_COUNT = 5

"""
We are using a semaphore to limit the number of concurrent calls to the APIs.
"""
sem = asyncio.Semaphore(SEMAPHORE_LIMIT)

"""
Decorator to limit the number of concurrent calls to the APIs.
"""
def limit_concurrency[**P, R](
    sem: asyncio.Semaphore | int,
) -> Callable[[Callable[P, Awaitable[R]]], Callable[P, Awaitable[R]]]:
    semaphore = asyncio.Semaphore(sem) if isinstance(sem, int) else sem

    def decorator(fn: Callable[P, Awaitable[R]]) -> Callable[P, Awaitable[R]]:
        @functools.wraps(fn)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            logger.info(f"{fn.__name__} is waiting for semaphore")
            async with semaphore:
                return await fn(*args, **kwargs)

        return wrapper

    return decorator

@limit_concurrency(sem)
async def openai_call(text: str) -> dict:
    """
    We are calling the OpenAI API.
    """

    logging.info(f"Calling to OpenAI for {text}")
    await asyncio.sleep(random.uniform(MIN_LATENCY, MAX_LATENCY))
    logger.info(f"OpenAI done for {text}")
    # Simulate a payload response
    return {"text": text}

@limit_concurrency(sem)
async def anthropic_call(text: str) -> dict:
    """
    We are calling the Anthropic API.
    """

    logging.info(f"Calling to Anthropic for {text}")
    await asyncio.sleep(random.uniform(MIN_LATENCY, MAX_LATENCY))
    logger.info(f"Anthropic done for {text}")
    # Simulate a payload response
    return {"text": text}

@limit_concurrency(sem)
async def llama_call(text: str) -> dict:
    """
    We are calling the Llama API.
    """

    logging.info(f"Calling to Llama for {text}")
    await asyncio.sleep(random.uniform(MIN_LATENCY, MAX_LATENCY))
    logger.info(f"Llama done for {text}")
    # Simulate a payload response
    return {"text": text}

# Entry point
async def main() -> None:
    """
    Main function to run the orchestrator.
    """

    tasks = []
    tasks.extend([openai_call(f"Hello OpenAI, {i}!") for i in range(OPENAI_TASKS_COUNT)])
    tasks.extend([anthropic_call(f"Hello Anthropic, {i}!") for i in range(ANTHROPIC_TASKS_COUNT)])
    tasks.extend([llama_call(f"Hello Llama, {i}!") for i in range(LLAMA_TASKS_COUNT)])
    try:
        start_time = time.perf_counter()
        async with asyncio.timeout(TIMEOUT):
            await asyncio.gather(*tasks, return_exceptions=True)
            logger.info(f"All tasks completed in {time.perf_counter() - start_time:.2f} seconds")
    except asyncio.TimeoutError:
        logger.error("Tasks timed out")


if __name__ == "__main__":
    asyncio.run(main())
