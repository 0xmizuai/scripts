from mizuscripts.types import Embedding
from mizuscripts.s3 import store_multi as s3_store_multi
import time
import queue

import chromadb
import hashlib
from openai import AsyncOpenAI

import asyncio
from asyncio import Semaphore, sleep

import os
import pathlib
from dotenv import load_dotenv

load_dotenv()
OPENAI_API_KEY = os.getenv('LEPTON_API_KEY')
LEPTON_API_BASE = os.getenv('LEPTON_API_BASE')

ROOT_DIR = pathlib.Path(__file__).parent.resolve()
BATCH_SIZE = 100


def gen_data_path(file: str):
    return pathlib.PurePath(ROOT_DIR, "../data/" + file)


client = chromadb.PersistentClient(path=str(gen_data_path("chroma")))
collection = client.get_or_create_collection("domains")


def local_store(e: Embedding):
    collection.add(documents=[e.text], embeddings=[e.embedding], ids=[e.id])


def local_store_multi(embeddings: list[Embedding]):
    ids = [embedding.id for embedding in embeddings]
    docs = [embedding.text for embedding in embeddings]
    embeddings = [embedding.embedding for embedding in embeddings]
    collection.add(documents=docs, embeddings=embeddings, ids=ids)


def gen_embedding_id(text: str, model: str = 'llama3-8b') -> str:
    return model + "/" + hashlib.sha256(text.encode()).hexdigest()


client = AsyncOpenAI(api_key=OPENAI_API_KEY, base_url=LEPTON_API_BASE)


async def gen_embedding_impl(
    text: str,
    model: str = 'llama3-8b'
) -> Embedding:
    id = gen_embedding_id(text, model)
    response = await client.embeddings.create(
        input=[text],
        model=model
    )
    embedding = response.data[0].embedding
    return Embedding(id=id, text=text, model=model, embedding=embedding)


async def query_embedding(text: str, model: str = 'llama3-8b'):
    e = await gen_embedding_impl(text, model)
    result = collection.query(
        query_embeddings=[e.embedding], n_results=2)
    print("querying embedding for {} and get {}".format(text, result))

q = queue.Queue(500000)


async def gen_embedding(
    sem: Semaphore,
    idx: int,
    text: str,
    model: str = 'llama3-8b'
) -> Embedding:
    async with sem:
        if idx % 100 == 0:
            print("processed {} domains...".format(idx))
        e = await gen_embedding_impl(text, model)
        q.put(e)


def dequeueAll(max=100) -> list[Embedding]:
    items = []
    while not q.empty() and max > 0:
        items.append(q.get())
        max -= 1
    return items


async def process_embeddings(total: int):
    print("processing embeddings...")
    while total > 0:
        items = dequeueAll()
        print("processing {} embeddings...".format(len(items)))
        if len(items) > 0:
            total -= len(items)
            t1 = time.time()
            local_store_multi(items)
            t2 = time.time()
            s3_store_multi(items)
            t3 = time.time()
            print(
                "processed {} embeddings, left is {}, cost {}s for local, {}s for s3.".format(
                    len(items),
                    total,
                    t2 - t1,
                    t3 - t2
                )
            )
        else:
            print("no item to process, sleeping for 3 seconds...")
            await sleep(3)


async def run():
    with open(gen_data_path("cleaned")) as f:
        domains = f.read().splitlines()
        tasks = [asyncio.create_task(process_embeddings(len(domains)))]
        sem = Semaphore(100)
        tasks += [
            asyncio.create_task(gen_embedding(sem, i, d)) for i, d in enumerate(domains)
        ]
        await asyncio.gather(*tasks)


async def test():
    await query_embedding("geology_and_science")
    await query_embedding("boat_wash_and_detail_services")
    await query_embedding("technology_infrastructure")


def main():
    asyncio.run(test())


if __name__ == '__main__':
    main()
