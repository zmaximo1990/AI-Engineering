import asyncio
import os

from openai import AsyncOpenAI

client = AsyncOpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
default_model = "gpt-4o-mini"
default_max_tokens = 100

async def call_openai(prompt: str, task_id: int) -> str:
    """Coroutine that makes one OpenAI chat completion call."""
    print(f"[task {task_id}] starting...")
    response = await client.chat.completions.create(
        model=default_model,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=default_max_tokens,
    )
    content = response.choices[0].message.content or ""
    print(f"[task {task_id}] done")
    return content


async def main() -> None:
    prompts = [
        "Say hello in one short sentence.",
        "Name one planet in the solar system.",
        "What is 2 + 2?",
        "Give me one color name.",
        "Name one programming language.",
    ]

    # 5 async tasks: each is a coroutine calling OpenAI
    tasks = [
        asyncio.create_task(call_openai(prompt, i + 1))
        for i, prompt in enumerate(prompts)
    ]

    results = await asyncio.gather(*tasks)

    print("\n--- Results ---")
    for i, result in enumerate(results, start=1):
        print(f"{i}. {result}")


if __name__ == "__main__":
    asyncio.run(main())
