from langchain.pydantic_v1 import BaseModel, Field
from typing import List

class ContentDomains(BaseModel):
    raw_str: str = Field(description="Raw string for the content domains")
    summary: str = Field(description="Summary string for the raw string")
    domains: List[str] = Field(description="List of domains the raw string is related to", default_factory=list)

    def get_dict(self):
        return {
            "raw": self.raw_str,
            "summary": self.summary,
            "domains": self.domains,
        } 