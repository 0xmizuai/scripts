import rich
import json
from rich.progress import Progress
from database.mongo import get_clustering_collection, get_domain_clustering_collection, get_training_data_collection


domain_clustering_collection = get_domain_clustering_collection()
clustering_collection = get_clustering_collection()
training_collection = get_training_data_collection()

subdomain_to_domain = {
    1: {},
    2: {},
    3: {},
}
domain_hieracy = {}
domains = set()
domain_clustering = domain_clustering_collection.find()
for domain in domain_clustering:
    level = domain["level"]
    for subdomain in domain["subdomains"]:
        subdomain_to_domain[level][subdomain] = domain["domain"]
        domains.add(subdomain)

for domain in domains:
    l1 = subdomain_to_domain[1][domain]
    l2 = subdomain_to_domain[2][domain]
    l3 = subdomain_to_domain[3][domain]

    if l1 not in domain_hieracy:
        domain_hieracy[l1] = {}
    
    if l2 not in domain_hieracy[l1]:
        domain_hieracy[l1][l2] = {}

    if l3 not in domain_hieracy[l1][l2]:
        domain_hieracy[l1][l2][l3] = []
    
    domain_hieracy[l1][l2][l3].append(domain)

with open("training_domains.json", "w") as f:
    f.write(json.dumps(domain_hieracy, indent=2))

page_size = 1000
total_source_data = clustering_collection.count_documents({})
processed = 0

res = []

with Progress() as progress:
    task = progress.add_task("Generating training data:", total=total_source_data)
    while processed < total_source_data:
        data = list(clustering_collection.find().limit(page_size).skip(processed))
        progress.advance(task_id=task, advance=len(data))
        for record in data:
            domains = record["domains"]
            summary = record["summary"]
            mapped_l1_domains = set()
            mapped_l2_domains = set()
            mapped_l3_domains = set()
            for domain in domains:
                if domain in subdomain_to_domain[1]:
                    mapped_l1_domains.add(subdomain_to_domain[1][domain])
                if domain in subdomain_to_domain[2]:
                    mapped_l2_domains.add(subdomain_to_domain[2][domain])
                if domain in subdomain_to_domain[3]:
                    mapped_l3_domains.add(subdomain_to_domain[3][domain])
            res.append({"text": summary, "l3_domains": list(mapped_l3_domains), "l2_domains": list(mapped_l2_domains), "l1_domains": list(mapped_l1_domains)})
        processed += len(data)
        rich.print(f"{processed}/{total_source_data}")

with open("raw_training.json", "w") as f:
    f.write(json.dumps(res))
