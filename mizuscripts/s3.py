import boto3

import hashlib
import os
from dotenv import load_dotenv

from multiprocessing import concurrent

load_dotenv()
R2_BASE_URL = os.getenv('R2_BASE_URL')
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
R2_BUCKET_NAME = os.getenv('R2_BUCKET_NAME')

from dataclasses import asdict
import json
from mizuscripts.types import Embedding

s3 = boto3.client('s3',
  endpoint_url = R2_BASE_URL,
  aws_access_key_id = AWS_ACCESS_KEY_ID,
  aws_secret_access_key = AWS_SECRET_ACCESS_KEY
)

def store_embedding(e: Embedding):
    id = hashlib.sha256(e.text.encode()).hexdigest() + "-" + e.model
    s3.upload_fileobj(
        json.dumps(asdict(e)),
        R2_BUCKET_NAME,
        '/category_embedding/{}'.format(id)
    )

BATCH_SIZE = 100
def store_embeddings(es: list[Embedding]):
    executor = concurrent.futures.ThreadPoolExecutor(BATCH_SIZE)
    futures = [executor.submit(store_embedding, e) for e in es]
    concurrent.futures.wait(futures)
