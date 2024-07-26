import boto3
import json
import os

from rich.progress import Progress
from huggingface_hub import login
from transformers import AutoTokenizer
from database.mongo import get_r2_stat_collection, get_r2_raw_collection
from concurrent.futures import ThreadPoolExecutor, wait, ALL_COMPLETED

login(token = os.getenv('HUGGING_FACE_TOKEN'))

R2_BASE_URL = f"{os.getenv('R2_BASE_URL')}/raw-data"
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
R2_BUCKET_NAME = os.getenv('R2_BUCKET_NAME')

raw_collection = get_r2_raw_collection()
stat_collection = get_r2_stat_collection()

executor = ThreadPoolExecutor(max_workers=150)

tokenizer = AutoTokenizer.from_pretrained('meta-llama/Meta-Llama-3-8B')

total_count = raw_collection.count_documents({})
stat_count= stat_collection.count_documents({})
speed = 1000
token_limit = 7500

def get_document_stat(key: str):
    s3 = boto3.client(
        's3',
        endpoint_url=R2_BASE_URL,
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    )
    dolma = s3.get_object(Bucket=R2_BUCKET_NAME, Key=r2_key)
    content = dolma["Body"].read().decode("utf-8")
    text = json.loads(content)["text"]
    tokenized_text = tokenizer.tokenize(text)
    return {
        "r2_key": key,
        "llama3_tokens": len(tokenized_text),
        "classified": False
    }


with Progress() as progress:
    task = progress.add_task("Adding stat for dolma data...", total=total_count, progress=stat_count)
    while stat_count < total_count:
        documents = list(raw_collection.find().limit(speed).skip(stat_count))
        executions = []
        for document in documents:
            executions.append(executor.submit(get_document_stat, document["r2_key"]))
        wait(executions, return_when=ALL_COMPLETED)
        stats = []
        for execution in executions:
            res = execution.result()
            stats.append(res)
        stat_collection.insert_many(stats)
        stat_count += len(stats)