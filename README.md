## Clustering
`poetry run python3 domain_cluster.py --level=level --count=count`
* level: 1-3, 3 will do clustring against all domains, 1-2 will based on level 2 or 3
* count: number of clusters to classify
* data available at: mizu/domain_clustering (in mongo) in format of `{level: int, domain: str: subdomains: [str]}`

## Training Data Generation
`poetry run python3 generate_training_data.py`

## Training
`poetry run python3 train.py`

## Connect to Document DB
1. SSH Tunnel: `ssh -i dolma.pem -L 27017:dolma-570746005621.us-east-1.docdb-elastic.amazonaws.com:27017 ubuntu@3.219.141.232 -N`
2. `mongo --sslAllowInvalidHostnames --ssl --username username --password password`