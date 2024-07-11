from database.mongo import get_domain_collection, get_domain_clustering_collection
from stores.domain_store import DomainStore
from agent.domain_summary_agent import DomainSummaryAgent
from sklearn.cluster import KMeans
from typing import List, Dict
from concurrent.futures import ThreadPoolExecutor, wait, ALL_COMPLETED


domain_collection = get_domain_collection()
clustering_collection = get_domain_clustering_collection()

all_domains = list(domain_collection.find())
domain_names = [domain["name"] for domain in all_domains]
documents = DomainStore(documents=domain_names).get_embeddings()

def cluster(documents:dict, n_clusters: int = 300):
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
groups = cluster(documents)

res = []
index = 0
for data in executor.map(categorize, groups.values()):
    res.append({"domains": groups[index], "clustered_domain": data})
    index += 1

clustering_collection.insert_many(res)