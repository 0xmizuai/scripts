import os
import json
from langchain.agents import AgentExecutor, create_react_agent
from langchain_openai import ChatOpenAI, OpenAI
from langchain_core.prompts import PromptTemplate
from agent.summary_tool import SummaryTool
from agent.revisit_tool import SummaryRevisitTool
from utils import chunk
from typing import List

OPENAI_API_KEY = os.getenv('LEPTON_API_KEY')
LEPTON_API_BASE = os.getenv('LEPTON_API_BASE')

class DomainSummaryAgent:
    def __init__(self):
        self.llm = OpenAI(api_key=OPENAI_API_KEY, base_url=LEPTON_API_BASE, model="llama3-8b", verbose=False)

    def invoke(self, domains: List[str]) -> List[str]:
        while True:
            try:
                res = self.llm.invoke(short_promopt % (",".join(domains)))
                if "{" in res and "}" in res:
                    start_index = res.find("{")
                    end_index = res.rfind("}")
                    return json.loads(res[start_index:end_index+1])["domain"]
            except:
                
                continue
        

short_promopt = """
    <|begin_of_text|><|start_header_id|>user<|end_header_id|>
    As a language expert, please give me a single domain that covers all domains in the list: %s. 
    Return a single domain in below format:
    {{
        "domain": "domain_name"
    }}
    <|start_header_id|>assistant<|end_header_id|>c:w

"""