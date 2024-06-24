from mizuscripts.types import Embedding
import json
from dataclasses import asdict
import boto3

import os
from dotenv import load_dotenv

from concurrent import futures

load_dotenv()
R2_BASE_URL = os.getenv('R2_BASE_URL')
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
R2_BUCKET_NAME = os.getenv('R2_BUCKET_NAME')


s3 = boto3.client('s3',
                  endpoint_url=R2_BASE_URL,
                  aws_access_key_id=AWS_ACCESS_KEY_ID,
                  aws_secret_access_key=AWS_SECRET_ACCESS_KEY
                  )


def gen_key(id: str) -> str:
    return 'category_embedding/{}'.format(id)


def store_obj(e: Embedding):
    s3.put_object(
        Bucket=R2_BUCKET_NAME,
        Body=json.dumps(asdict(e)),
        Key=gen_key(e.id)
    )


def store_multi(es: list[Embedding], batch_size: int = 100):
    executor = futures.ThreadPoolExecutor(batch_size)
    fs = [executor.submit(store_obj, e) for e in es]
    futures.wait(fs)


def get_obj(id: str) -> Embedding:
    obj = s3.get_object(
        Bucket=R2_BUCKET_NAME,
        Key=gen_key(id)
    )
    return Embedding(**json.loads(obj['Body'].read().decode('utf-8')))


def get_multi(ids: list[str], batch_size: int = 100) -> list[Embedding]:
    executor = futures.ThreadPoolExecutor(batch_size)
    fs = [executor.submit(get_obj, id) for id in ids]
    futures.wait(fs)
    return [f.result() for f in fs]
