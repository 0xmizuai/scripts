import numpy as np
from sklearn.cluster import KMeans

import chromadb
import os
import pathlib
from dotenv import load_dotenv

load_dotenv()
TEST_FLAG = True if os.getenv('TEST_FLAG') == 'true' else False
ROOT_DIR = pathlib.Path(__file__).parent.resolve()
DB_NAME = "chroma-test" if TEST_FLAG else "chroma"
COL_NAME = "domains-test" if TEST_FLAG else "domains"


def gen_data_path(file: str):
    return pathlib.PurePath(ROOT_DIR) / ".." / "data" / file


client = chromadb.PersistentClient(path=str(gen_data_path(DB_NAME)))
coll = client.get_or_create_collection(COL_NAME)


def get_embeddings() -> list[list[float]]:
    return coll.get(include=['embeddings'])


def cluster(embeds: list[list[float]], n_clusters: int = 100):
    kmeans_model = KMeans(n_clusters=n_clusters, random_state=0)
    classes = kmeans_model.fit_predict(embeds).tolist()
    print(classes)


def main():
    embeds = get_embeddings()
    cluster(embeds)


if __name__ == '__main__':
    main()
