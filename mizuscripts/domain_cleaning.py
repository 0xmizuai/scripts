import rich
import json
from rich.progress import Progress
from database.mongo import get_training_data_collection

training_collection = get_training_data_collection()
total_training_data = training_collection.count_documents({})
page_size = 1000
processed = 0
domain_count = {}
with Progress() as progress:
    task = progress.add_task("Generating training data:", total=total_training_data)
    while processed < total_training_data:
        data = list(training_collection.find().limit(page_size).skip(processed))
        progress.advance(task_id=task, advance=len(data))
        for record in data:
            domains = record["l3_domains"]
            for domain in domains:
                if domain not in domain_count:
                    domain_count[domain] = 1
                else:
                    domain_count[domain] = domain_count[domain] + 1
        processed += len(data)
        rich.print(f"{processed}/{total_training_data}")

minor_domains = set()
web_domains = set()
for domain, count in domain_count.items():
    if count < 10:
        minor_domains.add(domain)
    if "." in domain:
        print("potential domain name: {}".format(domain))
        web_domains.add(domain)

print("total minor domains are {}".format(len(minor_domains)))
print("total potential web domains are {}".format(len(web_domains)))

res = []
total_short_text = 0
data_with_no_domains = 0
processed = 0
with Progress() as progress:
    task = progress.add_task("Generating cleaned training data:", total=total_training_data)
    while processed < total_training_data:
        data = list(training_collection.find().limit(page_size).skip(processed))
        progress.advance(task_id=task, advance=len(data))
        for record in data:
            text = record["text"]
            if len(text.split(" ")) < 5:
                total_short_text = total_short_text + 1
            else:
                domains = record["l3_domains"]
                for domain in domains:
                    if domain in minor_domains or domain in web_domains:
                        domains.remove(domain)
                if len(domains) > 0:
                    res.append({"text": text, "domains": domains})
                else:
                    data_with_no_domains = data_with_no_domains + 1
        processed += len(data)
        rich.print(f"{processed}/{total_training_data}")

print("total short text data records is {}".format(total_short_text))
print("total data records with no domains is {}".format(data_with_no_domains))
print("total training data is {}".format(len(res)))

with open("cleaned_raw_training.json", "w") as f:
    f.write(json.dumps(res))
