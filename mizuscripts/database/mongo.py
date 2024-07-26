from mongoengine import *

import os
from dotenv import load_dotenv
from pymongo import MongoClient
connection_str = os.getenv("MONGO_DB_URL")
print(connection_str)
backup_mongo = os.getenv("MONGO_BACKUP")
mongo_client = MongoClient(connection_str, tls=True, tlsAllowInvalidCertificates=True)
client = mongo_client["mizu"]
backup_client = MongoClient(backup_mongo)["test-preprocessor"]
# client = MongoClient(connection_str)["mizu"]
# other_client = MongoClient(os.getenv("MONGO_DB_URL"))["mizu"]

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


def get_r2_stat_collection():
    return client["dolma_stat"]

def get_r2_raw_collection():
    return client["raw_data"]