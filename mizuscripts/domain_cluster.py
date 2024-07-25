import click
import rich
from rich.progress import Progress
from database.mongo import get_domain_collection, get_domain_clustering_collection
from stores.domain_store import DomainStore
from agent.domain_summary_agent import DomainSummaryAgent
from sklearn.cluster import KMeans
from typing import List, Dict
from concurrent.futures import ThreadPoolExecutor, wait, ALL_COMPLETED


domain_collection = get_domain_collection()
clustering_collection = get_domain_clustering_collection()
total_domains = domain_collection.count_documents({})
executor = ThreadPoolExecutor(100)

def do_cluster(documents:dict, n_clusters: int = 2000):
    groups: Dict[int, List[str]] = {}
    kmeans_model = KMeans(n_clusters=n_clusters, random_state=0)
    classes = kmeans_model.fit_predict(documents["embeddings"]).tolist()
    docs = documents["documents"]
    for i in range(len(classes)):
        aclass = classes[i]
        if aclass not in groups:
            groups[aclass] = []
        groups[aclass].append(docs[i])
    return groups

def categorize(domains: List[str]) -> str:
    agent = DomainSummaryAgent()
    res = agent.invoke(domains)
    # print(f"Domains: {domains}, clustering: {res}")
    return res

def cluster(domains, level, count, subdomains):
    documents = DomainStore(documents=domains).get_embeddings() 
    groups = list(do_cluster(documents, count).values())
    
    res: Dict[str, List[str]] = {}
    index = 0
    for data in executor.map(categorize, groups):
        if data not in res:
            res[data] = groups[index]
        else:
            res[data].extend(groups[index])
        rich.print(f"{count} left")
        index += 1
        count -= 1
    
    domain_clusterings = []
    for domain in res:
        all_subdomains = []
        if len(subdomains) != 0:
            for d in res[domain]:
                all_subdomains.extend(subdomains[d])
        else:
            all_subdomains = res[domain]
        rich.print(f"{res[domain]} are under domain: {domain} with actual {len(all_subdomains)} domains")

        domain_clusterings.append({"domain": domain, "subdomains": all_subdomains, "level": level})
    
    clustering_collection.insert_many(domain_clusterings)

@click.command()
@click.option("--level", help="Level of the cluster", type=int)
@click.option("--count", help="count of domains to cluster into", type=int)
def run(level: int, count: int):
    page_size = 10000
    all_domains = []
    subdomain_map = {}
    if level == 3:
        with Progress() as progress:
            task = progress.add_task("Loading domains", total=total_domains)
            while len(all_domains) != total_domains:
                fetched_domains = list(domain_collection.find().limit(page_size).skip(len(all_domains)))
                progress.advance(task_id=task, advance=len(fetched_domains))
                all_domains.extend([domain["name"] for domain in fetched_domains])
    else:
        level_domains = list(clustering_collection.find({"level": level + 1}))
        speed = 10
        with Progress() as progress:
            task = progress.add_task(f"Loading L{level} domains", total=len(level_domains))
            while len(all_domains) != len(level_domains):
                fetched_domains = list(clustering_collection.find({"level": level + 1}).limit(speed).skip(len(all_domains)))
                progress.advance(task_id=task, advance=len(fetched_domains))
                all_domains.extend([domain["domain"] for domain in fetched_domains])
                for domain in fetched_domains:
                    subdomain_map[domain["domain"]]  = domain["subdomains"]

    rich.print(f"Fetched {len(all_domains)} batches domains")
    
    cluster(all_domains, level, count, subdomain_map)

if __name__ == "__main__":
    run()

