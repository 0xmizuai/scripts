from typing import List
from langchain.pydantic_v1 import BaseModel, Field
from database.mongo import get_domain_collection

class Domain(BaseModel):
    name: str = Field(description="Name of the domain")
    repo_id: int = Field(description="id of the domain's repo")

    @staticmethod
    def get_existing_domains(names: List[str]) -> List["Domain"]:
        collection = get_domain_collection()
        domains = list(collection.find({"name": {"$in": names}}))
        return [Domain(name=domain["name"], repo_id=domain["repo_id"]) for domain in domains]
    
    def get_dict(self) -> dict:
        return {
            "name": self.name,
            "repo_id": self.repo_id,
        }