# Load env as soon as possible
from dotenv import load_dotenv
load_dotenv()

import argparse
import asyncio
import logging
from llm import BaseLLMClient
from factory import LLMFactory
from schemas import ChatMessage, LLMConfig, Provider, Role

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run LLM chat demos across providers.")
    parser.add_argument(
        "--chat",
        action="store_true",
        default=False,
        help="Run chat() on selected clients (default: off)",
    )
    parser.add_argument(
        "--chat-stream",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Run chat_stream() on selected clients (default: on)",
    )
    parser.add_argument(
        "--openai",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Include the OpenAI provider (default: on)",
    )
    parser.add_argument(
        "--anthropic",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Include the Anthropic provider (default: on)",
    )
    parser.add_argument(
        "--gemini",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Include the Gemini provider (default: off)",
    )
    return parser.parse_args()


async def run_chat(client: BaseLLMClient, messages: list[ChatMessage]) -> None:
    """Invoke chat and print the ModelResponse."""
    label = client.provider.value
    try:
        response = await client.chat(messages)
    except Exception as exc:
        print(f"{label}: ERROR — {exc}")
        print("-" * 80)
        return

    if response.error:
        print(f"{label}: ERROR — {response.error}")
    else:
        print(f"{label}: {response.content}")
    print("-" * 80)


async def run_chat_stream(client: BaseLLMClient, messages: list[ChatMessage]) -> None:
    """Consume chat_stream and print chunks as they arrive."""
    label = client.provider.value
    print(f"{label}: ", end="", flush=True)
    try:
        async for chunk in client.chat_stream(messages):
            print(chunk, end="", flush=True)
        print()
    except Exception as exc:
        print(f"\n{label}: ERROR — {exc}")
    print("-" * 80)


def build_clients(
    *,
    openai_enabled: bool,
    anthropic_enabled: bool,
    gemini_enabled: bool,
) -> list[BaseLLMClient]:
    """Create clients only for the providers that were enabled via CLI flags.

    Providers whose API key is missing/empty are skipped with an error log
    instead of aborting the whole run.
    """
    configs: list[LLMConfig] = []
    if openai_enabled:
        configs.append(LLMConfig(provider=Provider.OPENAI))
    if anthropic_enabled:
        configs.append(LLMConfig(provider=Provider.ANTHROPIC))
    if gemini_enabled:
        configs.append(LLMConfig(provider=Provider.GEMINI))

    clients: list[BaseLLMClient] = []
    for config in configs:
        try:
            clients.append(LLMFactory.create_client(config))
        except ValueError as exc:
            logger.error("Skipping %s: %s", config.provider.value, exc)
    return clients


async def main(
    *,
    run_chat_enabled: bool,
    run_chat_stream_enabled: bool,
    openai_enabled: bool,
    anthropic_enabled: bool,
    gemini_enabled: bool,
) -> None:
    if not run_chat_enabled and not run_chat_stream_enabled:
        logger.error("Nothing to run: enable --chat and/or --chat-stream")
        return

    if not any((openai_enabled, anthropic_enabled, gemini_enabled)):
        logger.error(
            "Nothing to run: enable at least one provider "
            "(--openai / --anthropic / --gemini)"
        )
        return

    message = input("Enter your message: ").strip()
    if not message:
        logger.error("Empty message; aborting")
        return

    logger.info("Message received: %s", message)

    messages = [
        ChatMessage(role=Role.SYSTEM, content="You are a helpful assistant."),
        ChatMessage(role=Role.USER, content=message),
    ]

    clients = build_clients(
        openai_enabled=openai_enabled,
        anthropic_enabled=anthropic_enabled,
        gemini_enabled=gemini_enabled,
    )
    if not clients:
        logger.error(
            "No providers available: configure API keys for the selected providers"
        )
        return

    logger.info(
        "Providers selected: %s",
        ", ".join(client.provider.value for client in clients),
    )

    if run_chat_enabled:
        logger.info("Running chat() on selected clients in parallel")
        print("\n--- chat() Results ---")
        await asyncio.gather(*(run_chat(client, messages) for client in clients))

    if run_chat_stream_enabled:
        # Stream one provider at a time so chunks don't interleave in the console.
        logger.info("Running chat_stream() on selected clients sequentially")
        print("\n--- chat_stream() Results ---")
        for client in clients:
            await run_chat_stream(client, messages)

    logger.info("Finished")


if __name__ == "__main__":
    args = parse_args()
    asyncio.run(
        main(
            run_chat_enabled=args.chat,
            run_chat_stream_enabled=args.chat_stream,
            openai_enabled=args.openai,
            anthropic_enabled=args.anthropic,
            gemini_enabled=args.gemini,
        )
    )
