# Load env as soon as possible
from itertools import chain
from dotenv import load_dotenv

load_dotenv()

import asyncio
import json
import os
import logging
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

MODEL = os.getenv("MODEL", "gpt-4o")
TEMPERATURE = os.getenv("TEMPERATURE", 0.7)
API_KEY = os.getenv("API_KEY")

model = ChatOpenAI(model=MODEL, temperature=TEMPERATURE, api_key=API_KEY)
parser = StrOutputParser()

prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You extract technical entities from a software architecture description "
            "or an error log. Write technical summary as one concise English sentence.",
        ),
        ("human", "{text}"),
    ]
)

chain = prompt | model | StrOutputParser()

async def main() -> None:
    result = await chain.ainvoke({"text": "The system is built with React and Node.js."})
    print(result)

if __name__ == "__main__":
    asyncio.run(main())
