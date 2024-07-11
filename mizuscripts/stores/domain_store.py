import rich

from langchain.pydantic_v1 import BaseModel
from database.mongo import get_domain_collection
from langchain_chroma import Chroma
from langchain_core.vectorstores import VectorStoreRetriever
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from typing import List, Optional

class DomainStore():
    THRESHOLD = 0.90
    documents: List[str]

    def __init__(self, documents: List[str]):
        self.documents = "\n\n".join(documents)
    
    def vector_store(self) -> Optional[Chroma]:
        splitter = RecursiveCharacterTextSplitter(chunk_size=1, chunk_overlap=0, separators=["\n\n"], keep_separator=False)
        if len(self.documents) == 0:
            return None
        documents = splitter.create_documents([self.documents])
        return Chroma.from_documents(splitter.split_documents(documents), OpenAIEmbeddings())
    
    def get_embeddings(self):
        return self.vector_store().get(include=["embeddings", "documents"])
    