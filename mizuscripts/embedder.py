import chromadb
import hashlib
from openai import AsyncOpenAI

import asyncio
from asyncio import Semaphore

import os
import pathlib
from dotenv import load_dotenv

from typing import Awaitable

load_dotenv()
OPENAI_API_KEY = os.getenv('LEPTON_API_KEY')
LEPTON_API_BASE= os.getenv('LEPTON_API_BASE')

ROOT_DIR = pathlib.Path(__file__).parent.resolve()

from mizuscripts.s3 import store_multi as s3_store_multi
from mizuscripts.types import Embedding

def gen_data_path(file: str):
    return pathlib.PurePath(ROOT_DIR, "../data/" + file)

client = chromadb.Client()
collection = client.create_collection("domains")
def local_store_multi(embeddings: list[Embedding]):
    ids = [embedding.id for embedding in embeddings]
    docs = [embedding.text for embedding in embeddings]
    embeddings = [embedding.embedding for embedding in embeddings]
    collection.add(documents=docs, embeddings=embeddings, ids=ids)

async def query_embedding(sem: Semaphore, text: str, model: str = 'llama3-8b'):
    print("querying embedding for {}".format(text))
    e = await gen_embedding(sem, text, model)
    result = collection.query(query_embeddings=[e.embedding], n_results=2)
    print(result)

async def gen_embedding(
    sem: Semaphore,
    text: str,
    model: str = 'llama3-8b'
) -> Embedding:
    async with sem:
        id = hashlib.sha256(text.encode()).hexdigest() + "-" + model
        print("Generating embedding for {} with id {}".format(text, id))
        client = AsyncOpenAI(api_key=OPENAI_API_KEY, base_url=LEPTON_API_BASE)
        response = await client.embeddings.create(
            input = [text],
            model=model
        )
        embedding = response.data[0].embedding
        return Embedding(id=id, text=text, model=model, embedding=embedding)

async def gen_and_store_multi(sem: Semaphore, docs: list[str]):
    tasks = [asyncio.create_task(gen_embedding(sem, doc)) for doc in docs]
    embeddings = await asyncio.gather(*tasks)
    local_store_multi(embeddings)
    s3_store_multi(embeddings)

BATCH_SIZE = 100
def main():
    sem = asyncio.Semaphore(BATCH_SIZE)
    with open(gen_data_path("sample")) as f:
        domains = f.readlines()
        asyncio.run(gen_and_store_multi(sem, docs=domains))
    asyncio.run(query_embedding(sem, "geology_and_science"))

if __name__ == '__main__':
  main()
