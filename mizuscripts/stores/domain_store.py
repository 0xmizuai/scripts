import rich

from database.mongo import get_domain_collection
from langchain_chroma import Chroma
from langchain_core.vectorstores import VectorStoreRetriever
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from typing import List, Optional

class DomainStore():
    THRESHOLD = 0.90
    documents: List[str]
    store: VectorStoreRetriever

    def __init__(self):
        collection = get_domain_collection()
        self.documents = "\n\n".join([domain["name"] for domain in collection.find()])
        self.store = self.vector_store()
    
    def vector_store(self) -> Optional[Chroma]:
        splitter = RecursiveCharacterTextSplitter(chunk_size=1, chunk_overlap=0, separators=["\n\n"], keep_separator=False)
        if len(self.documents) == 0:
            return None
        documents = splitter.create_documents([self.documents])
        return Chroma.from_documents(splitter.split_documents(documents), OpenAIEmbeddings()).as_retriever(search_type="similarity_score_threshold", search_kwargs={"score_threshold": DomainStore.THRESHOLD})
    
    def search(self, domain: str) -> Optional[str]:
        if self.store is None:
            return None
        documents = self.store.invoke(f"{domain}") 
        if len(documents) == 0:
            return None
        return documents[0].page_content
