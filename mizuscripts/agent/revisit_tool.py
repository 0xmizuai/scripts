import json
from typing import Dict, Optional, Tuple
from typing import List
from langchain.callbacks.manager import (AsyncCallbackManagerForToolRun)
from langchain_openai import OpenAI
from langchain.tools import BaseTool

class SummaryRevisitTool(BaseTool):
    name = "summary_revisit"
    description = "useful when trying to make sure that a domain is related to the text"
    llm: OpenAI
    
    def _to_args_and_kwargs(self, tool_input: str | Dict) -> Tuple[Tuple, Dict]:
        inputs = json.loads(tool_input)
        return (), inputs

    def _run(
            self, domain: str, text: str, _:Optional[AsyncCallbackManagerForToolRun] = None
    ):
        return self.llm.invoke(f"Please answer yes or no to the question next. Does the main idea of text below related to domain: {domain}? Do not try to answer any other questions or make up new questions\n {text}")