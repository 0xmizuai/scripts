import rich
from rich.progress import Progress
from database.mongo import client, backup_client

for collection in list(backup_client.list_collections()):
    name = collection["name"]
    backup_collection = backup_client[name]
    collection = client[name]
    total_backup_count = backup_collection.count_documents({})
    existing_counts = collection.count_documents({})
    speed = 10000
    while existing_counts != total_backup_count:
        documents = list(backup_collection.find().limit(speed).skip(existing_counts))
        existing_counts += len(documents)
        collection.insert_many(documents)
        rich.print(f"{existing_counts}/{total_backup_count} done for collection {name}")
