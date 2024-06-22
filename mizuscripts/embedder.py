import chromadb
import hashlib
from openai import AsyncOpenAI

import asyncio
from asyncio import Semaphore

import os
from dotenv import load_dotenv

load_dotenv()
OPENAI_API_KEY = os.getenv('LEPTON_API_KEY')
LEPTON_API_BASE= os.getenv('LEPTON_API_BASE')

client = chromadb.Client()
collection = client.create_collection("domains")

BATCH_SIZE = 100

def store_multi(docs: list[str], embeddings: list[list[float]]):
    ids = [hashlib.sha256(doc.encode()).hexdigest() for doc in docs]
    collection.add(documents=docs, embeddings=embeddings, ids=ids)

async def gen_embedding(text: str, sem: Semaphore) -> asyncio.Awaitable[list[float]]:
    async with sem:
        client = AsyncOpenAI(api_key=OPENAI_API_KEY, api_base=LEPTON_API_BASE)
        return await client.embeddings.create(
            input = [text],
            model='llama3-8b'
        ).data[0].embedding

async def gen_and_store_multi(docs: list[str]):
    sem = asyncio.Semaphore(BATCH_SIZE)
    tasks = [asyncio.create_task(gen_embedding(doc, sem)) for doc in docs]
    embeddings = await asyncio.gather(*tasks)
    return await store_multi(docs, embeddings)
