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

count = 0
page_size = 500
all_domains = []
with Progress() as progress:
    task = progress.add_task("Loading domains", total=total_domains)
    while len(all_domains) != total_domains:
        fetched_domains = list(domain_collection.find().limit(page_size).skip(len(all_domains)))
        progress.advance(task_id=task, advance=len(fetched_domains))
        all_domains.extend(fetched_domains)

domain_names = [domain["name"] for domain in all_domains]
documents = DomainStore(documents=domain_names).get_embeddings()

def cluster(documents:dict, n_clusters: int = 2000):
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
    print(f"Domains: {domains}, clustering: {res}")
    return res


executor = ThreadPoolExecutor(100)
groups = cluster(documents).values()

res: Dict[str, List[str]] = {}
index = 0
for data in executor.map(categorize, groups):
    if data not in res:
        res[data] = groups[index]
    else:
        res[data].extend(groups[index])
    index += 1

domain_clusterings = []
for domain in res:
    domain_clusterings.append({"domain": domain, "subdomains": res[domain]})

clustering_collection.insert_many(domain_clusterings)