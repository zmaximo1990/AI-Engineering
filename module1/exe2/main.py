import asyncio
import logging

from factory import create_llm_client

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


async def main() -> None:
    message = input("Enter your message: ").strip()
    if not message:
        logger.error("Empty message; aborting")
        return

    logger.info("Message received: %s", message)

    openai_client = create_llm_client({"provider": "openai"})
    anthropic_client = create_llm_client({"provider": "anthropic"})
    # Increase max tokens to 1024 to take into account Gemini thinking tokens
    gemini_client = create_llm_client({"provider": "gemini", "max_tokens": 1024})

    logger.info("Running chat() on both clients in parallel")
    openai_answer, anthropic_answer, gemini_answer = await asyncio.gather(
        openai_client.chat(message),
        anthropic_client.chat(message),
        gemini_client.chat(message),
        return_exceptions=True # propagate exceptions to the caller to avoid break other providers errors if one fails
    )

    print("\n--- Results ---")
    print(f"OpenAI:    {openai_answer}")
    print("-" * 80)
    print(f"Gemini:    {gemini_answer}")
    print("-" * 80)
    print(f"Anthropic: {anthropic_answer}")
    print("-" * 80)

    logger.info("Finished")


if __name__ == "__main__":
    asyncio.run(main())
