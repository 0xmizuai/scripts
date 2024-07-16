import rich
from rich.progress import Progress
from database.mongo import get_clustering_collection, get_domain_clustering_collection, get_training_data_collection, get_tb_training_collection
from transformers import AutoTokenizer

import os
from dotenv import load_dotenv

load_dotenv()

page_size = 1000
TINY_BERT = os.getenv("MODEL_TINEY_BERT")


def get_domain_cluster_mapping():
    domain_clustering_collection = get_domain_clustering_collection()
    subdomain_to_domain = {}
    domain_clusterings = domain_clustering_collection.find()
    for domain in domain_clusterings:
        for subdomain in domain_clusterings[domain]:
            subdomain_to_domain[subdomain] = domain
    return subdomain_to_domain


def gen_traning_data():
    subdomain_to_domain = get_domain_cluster_mapping()

    clustering_collection = get_clustering_collection()
    training_collection = get_training_data_collection()

    total_source_data = clustering_collection.count_documents({})
    processed = 0
    with Progress() as progress:
        task = progress.add_task("Generating training data:")
        while processed < total_source_data:
            res = []
            data = clustering_collection.find().limit(page_size).skip(processed)
            progress.advance(task_id=task, advance=len(data))
            for record in data:
                domains = record["domains"]
                summary = record["summary"]
                mapped_domains = set()
                for domain in domains:
                    mapped_domains.add(subdomain_to_domain[domain])
                res.append({"text": summary, "domains": list(mapped_domains)})
            training_collection.insert_many(res)
            processed += len(data)
            rich.print(f"{processed}/{total_source_data}")


def gen_segments(tokens, max_size=510):
    segments = []
    total_batch = len(tokens) // max_size
    for b in range(1, total_batch):
        segment = tokens[b * max_size: (b + 1) * max_size]
        segments.append(segment)
    return segments


def gen_tb_traning_data():
    training_coll = get_training_data_collection()
    tb_training_coll = get_tb_training_collection()

    tokenizer = AutoTokenizer.from_pretrained()
    total_training_data = training_coll.count()
    processed = tb_training_coll.count()
    with Progress() as progress:
        task = progress.add_task("Generating tinyBert training data:")
        while processed < total_training_data:
            res = []
            data = training_coll.find().limit(page_size).skip(processed)
            progress.advance(task_id=task, advance=len(data))
            for record in data:
                tokens = tokenizer.tokenize(
                    record["text"], add_special_tokens=False)
                segments = gen_segments(tokens)
                for segment in segments:
                    for domain in record["domains"]:
                        res.append(
                            {"source": data.id, "segment": segment, "domain": domain})
            tb_training_coll.insert_many(res)
            processed += len(data)
            rich.print(f"{processed}/{total_training_data}")


def main():
    gen_tb_traning_data()


if __name__ == "__main__":
    main()