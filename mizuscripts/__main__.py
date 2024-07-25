import time
import json
import random
from os.path import exists
from os import remove
import requests
import rich
import click
from datetime import datetime
import gzip
import asyncio
import os
from typing import List, Set, Dict
from sh import gunzip

import rich.progress
from agent.domain_agent import DomainAgent
from stores.domain_store import DomainStore
from agent.summary_tool import SummaryTool
from langchain_openai import OpenAI
from utils import chunk
from pypdf import PdfReader 
from multiprocessing.pool import ThreadPool
from pathlib import Path
from model.content import ContentDomains
from model.domain import Domain
from database.mongo import get_clustering_collection, get_domain_collection, get_processed_collection, get_processed_dolma_collection, get_subdomain_collection
from rich.progress import Progress
from util.string import hash
from langchain_chroma import Chroma

OPENAI_API_KEY = os.getenv('LEPTON_API_KEY')
LEPTON_API_BASE = os.getenv('LEPTON_API_BASE')

clustering_collection = get_clustering_collection()
domain_collection = get_domain_collection()
processed_collection = get_processed_collection()
similar_domain_collection = get_subdomain_collection()

def get_chunk_summary(content: str, index: int):
    llm = OpenAI(api_key=OPENAI_API_KEY, base_url=LEPTON_API_BASE, model="llama3-8b-instruct", timeout=10)
    tool = SummaryTool(llm=llm)
    start = datetime.now()
    # rich.print(f"Tool number: {index}, starts at: {start.strftime("%Y-%m-%d %H:%M:%S")}")
    res = tool._run(content)
    end = datetime.now()
    rich.print(f"Tool number: {index}, ends at: {end.strftime("%Y-%m-%d %H:%M:%S")}, duration: {(end - start).seconds}")
    # on_summary((res, index))
    return (res, index)

async def get_summary(content: str) -> str:
    res = content
    while len(res) >= DomainAgent.MAXIMAL_CONTEXT_SIZE:
        pool = ThreadPool(30)
        chunks = chunk(res, DomainAgent.MAXIMAL_CONTEXT_SIZE // 2, DomainAgent.BUFFER_SIZE)
        chunk_res = [""] * len(chunks)
        def on_summary(result):
            chunk_res[result[1]] = result[0]
        for i in range(len(chunks)):
            pool.apply_async(get_chunk_summary, args=(chunks[i], i,), callback=on_summary)
        pool.close()
        pool.join()
        res = "".join(chunk_res)
    return res

def categorize(content: str, agent: DomainAgent):
    content_hash = hash(content)
    processed_res = processed_collection.find_one({"hash": content_hash})
    if processed_res is not None:
        rich.print(f"Skip processed hash: {content_hash}")
        return
    else:
        rich.print(f"Processeing hash: {content_hash}")

    # store = DomainStore()
    summary = asyncio.run(get_summary(content))
    domains = agent.invoke(summary)
    save(domains, content, summary)

def save(domains: List[str], content: str, summary: str):
    # First save content domains
    content_domain = ContentDomains(raw_str=content, domains=domains, summary=summary)
    content_id = clustering_collection.insert_one(content_domain.get_dict()).inserted_id
    processed_collection.insert_one({"hash": hash(content_domain.raw_str), "content_id": content_id})

    # Next store new domains
    existing_domains = [domain.name for domain in Domain.get_existing_domains(domains)]
    new_domain_names = list(filter(lambda domain: domain not in existing_domains, domains))
    new_domains: List[Domain] = [Domain(name=domain, repo_id=0) for domain in new_domain_names]
    domain_collection.insert_many([domain.get_dict() for domain in new_domains])

    # Third figure out the relationship between domains
    # similar_domains: List[Dict] = []
    # for domain in new_domains:
    #     parent_domain = store.search(domain) 
    #     if parent_domain is not None:
    #         similar_domains.append({"domain": parent_domain, "subdomain": domain})
    #         similar_domains[domain] = parent_domain
    # if len(similar_domains) > 0:
    #     similar_domain_collection.insert_many(similar_domains)
    
    # Finally log the data
    rich.print(json.dumps({
        "raw_str": content,
        "summary": summary,
        "domains": domains,
        # "subdomains": similar_domains,
    }, indent=2, default=list))

def download_and_extract(id: int, dir: str) -> str:
    name = str(id).zfill(4)
    file_name_prefix = f"{dir}/{name}"
    if not exists(f"{file_name_prefix}.json"):
        if not exists(f"{file_name_prefix}.json.gz"):
            url = f"https://olmo-data.org/dolma-v1_7/c4-filtered/c4-{name}.json.gz"
            response = requests.get(url, stream=True)
            total_length = response.headers.get('content-length')
            print(total_length)
            with open(f"{file_name_prefix}.json.gz", "wb") as f:
                with Progress() as progress:
                    task = progress.add_task(f"[cyan]Downloading {name}.json.gz", total=total_length)
                    for data in response.iter_content(chunk_size=1024):
                        progress.update(task_id=task, advance=len(data))
                        f.write(data)
    
        gunzip(f"{file_name_prefix}.json.gz")
    return f"{file_name_prefix}.json"

def remove_file(file: str):
    if exists(file):
        remove(file)

def clean_up(id: int, dir: str):
    name = str(id).zfill(4)
    file_name_prefix = f"{dir}/{name}"
    remove_file(f"{file_name_prefix}.json.gz")
    remove_file(f"{file_name_prefix}.json")


def fetch_next(dir: str) -> str:
    collection = get_processed_dolma_collection()
    processed_ids = [int(processed["id"]) for processed in collection.find()]
    next = max(processed_ids) + 1 if len(processed_ids) > 0 else 1
    return download_and_extract(next, dir)

def process(dir: str):
    next =  fetch_next(dir)
    rich.print(f"Processing json: {next}")
    llm = OpenAI(api_key=OPENAI_API_KEY, base_url=LEPTON_API_BASE, model="llama3-8b", verbose=False)
    agent = DomainAgent(llm=llm)
    pool = ThreadPool(100)
    random.seed(datetime.now().timestamp())
    with open(next, "r") as f:
        while True:
            record = f.readline()
            if not record:
                break
            if random.random() >= 0.2:
                continue
            text = json.loads(record)["text"]
            pool.apply_async(categorize, (text, agent,))
    pool.close()
    pool.join()
    collection = get_processed_dolma_collection()
    collection.insert_one({"id": next.split("/")[-1].split(".")[0]})

    remove_file(next)


@click.command()
@click.option("--dir", help="directory to store all binaries")
def run(dir: str = "/Users/wangjunhong/tmp"):
    while True:
        collection = get_processed_dolma_collection()
        processed_count = len(list(collection.find()))
        if processed_count == 100:
            return
        process(dir)


def main():
    run()

if __name__ == "__main__":
    main()