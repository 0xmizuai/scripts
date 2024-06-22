import boto3

import os
from dotenv import load_dotenv

from concurrent import futures

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

def store(e: Embedding):
    s3.upload_fileobj(
        json.dumps(asdict(e)),
        R2_BUCKET_NAME,
        '/category_embedding/{}'.format(e.id)
    )

def store_multi(es: list[Embedding], batch_size: int = 100):
    executor = futures.ThreadPoolExecutor(batch_size)
    futures = [executor.submit(store, e) for e in es]
    futures.wait(futures)
