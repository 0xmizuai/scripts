import rich
from rich.progress import Progress
from database.mongo import get_clustering_collection, get_domain_clustering_collection, get_training_data_collection


domain_clustering_collection = get_domain_clustering_collection()
clustering_collection = get_clustering_collection()
training_collection = get_training_data_collection()

subdomain_to_domain = {}
domain_clusterings = domain_clustering_collection.find()
for domain in domain_clusterings:
    for subdomain in domain_clusterings[domain]:
        subdomain_to_domain[subdomain] = domain

page_size = 1000
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