from mizuscripts.types import Embedding
from mizuscripts.s3 import store_multi as s3_store_multi
import time
import queue

import chromadb
import hashlib
from openai import AsyncOpenAI

import asyncio
from asyncio import Semaphore
import threading

import os
import pathlib
from dotenv import load_dotenv

load_dotenv()
OPENAI_API_KEY = os.getenv('LEPTON_API_KEY')
LEPTON_API_BASE = os.getenv('LEPTON_API_BASE')
TEST_FLAG = True if os.getenv('TEST_FLAG') == 'true' else False

ROOT_DIR = pathlib.Path(__file__).parent.resolve()
BATCH_SIZE = 100


def gen_data_path(file: str):
    return pathlib.PurePath(ROOT_DIR, "../data/" + file)


DB_NAME = "chroma-test" if TEST_FLAG else "chroma"
client = chromadb.PersistentClient(path=str(gen_data_path(DB_NAME)))
COL_NAME = "domains-test" if TEST_FLAG else "domains"
collection = client.get_or_create_collection(COL_NAME)


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
MAX_QUEUED = 500


async def enqueue_one(e: Embedding):
    if q.qsize() > MAX_QUEUED:
        await asyncio.sleep(3)
        await enqueue_one(e)
    else:
        q.put(e)


async def gen_embedding(
    sem: Semaphore,
    idx: int,
    text: str,
    model: str = 'llama3-8b'
) -> Embedding:
    async with sem:
        if idx % BATCH_SIZE == 0:
            print("generated embedding for {} domains...".format(idx))
        e = await gen_embedding_impl(text, model)
        await enqueue_one(e)


async def gen_embeddings(sem: Semaphore, domains: list[str]):
    tasks = [
        asyncio.create_task(gen_embedding(sem, i, d)) for i, d in enumerate(domains)
    ]
    await asyncio.gather(*tasks)


def dequeueAll(max=100) -> list[Embedding]:
    items = []
    while not q.empty() and max > 0:
        items.append(q.get())
        max -= 1
    return items


def process_embeddings(total: int):
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
            time.sleep(3)


def run():
    file = "sample" if TEST_FLAG else "cleaned"
    with open(gen_data_path(file)) as f:
        domains = f.read().splitlines()
        consumer = threading.Thread(
            target=process_embeddings, args=[len(domains)])
        consumer.start()
        asyncio.run(gen_embeddings(Semaphore(100), domains))
        consumer.join()


async def test():
    await query_embedding("geology_and_science")
    await query_embedding("boat_wash_and_detail_services")
    await query_embedding("technology_infrastructure")


def main():
    run()


if __name__ == '__main__':
    main()
