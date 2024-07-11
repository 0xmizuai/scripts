from langchain.pydantic_v1 import BaseModel, Field
from typing import Dict

class UnionFindNode(BaseModel):
    parent: "UnionFindNode" = Field(description="Parent node of this node")
    value: str = Field(description="Value of the node")

class UnionFind(BaseModel):
    nodes: Dict[str, UnionFindNode] = Field(description="dict of all nodes", default_factory=dict)