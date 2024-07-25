import rich

from rich.progress import Progress
from langchain.pydantic_v1 import BaseModel
from database.mongo import get_domain_collection
from langchain_chroma import Chroma
from langchain_core.vectorstores import VectorStoreRetriever
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from typing import List, Optional
from utils import chunk

def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

class DomainStore():
    THRESHOLD = 0.90
    documents: List[str]

    def __init__(self, documents: List[str]):
        self.documents = "\n\n".join(documents)
    
    def vector_store(self) -> Optional[Chroma]:
        splitter = RecursiveCharacterTextSplitter(chunk_size=1, chunk_overlap=0, separators=["\n\n"], keep_separator=False)
        if len(self.documents) == 0:
            return None
        splits = splitter.create_documents([self.documents])
        documents = list(chunks(splits, 2000))
        chroma = None
        # with Progress() as progress:
        # task = progress.add_task("Constructing chroma database:", total=len(splits))
        finished = 0
        for document in documents:
            if chroma is None:
                chroma = Chroma.from_documents(document, OpenAIEmbeddings(model="text-embedding-3-small", dimensions=300))
            else:
                chroma.add_documents(document)
            finished += len(document)
            rich.print(f"{finished}/{len(splits)} finished")
        return chroma
    
    def get_embeddings(self):
        return self.vector_store().get(include=["embeddings", "documents"])
    
