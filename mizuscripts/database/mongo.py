from mongoengine import *

import os
from dotenv import load_dotenv
from pymongo import MongoClient
connection_str = os.getenv("MONGO_DB_URL")
client = MongoClient(connection_str, tls=True, tlsAllowInvalidCertificates=True)["mizu"]

def get_training_data_collection():
    return client["training"]

def get_clustering_collection():
    return client["clustering"]

def get_domain_collection():
    return client["domain"]

def get_domain_clustering_collection():
    return client["domain_clustering"]

def get_processed_collection():
    return client["processed"]

def get_processed_dolma_collection():
    return client["processed_dolma"]


def get_subdomain_collection():
    return client["subdomains"]
