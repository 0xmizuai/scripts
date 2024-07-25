import json
import os
from typing import Optional
from langchain.callbacks.manager import (AsyncCallbackManagerForToolRun)
from langchain_openai import OpenAI
from langchain.tools import BaseTool

class SummaryTool(BaseTool):
    name = "summary"
    description = "useful when trying to summarize what a text is saying"
    llm: OpenAI

    async def _arun(
            self, query: str, _:Optional[AsyncCallbackManagerForToolRun] = None
    ):
        # res = self.llm.invoke(f"As a language expert, please summary the given text: {query}. Return the result in format:").strip()
        while True:
            try:
                res = await self.llm.ainvoke(prompt % query)
                start_index = res.find("{")
                end_index = res.rfind("}")
                summary = res[start_index:end_index + 1]
                return json.loads(summary)["summary"]
            except:
                continue
        # summary = json.loads(res)
        # return summary["summary"]
        # while True:
        #     try:
        #         res = await self.llm.ainvoke(prompt % query)
        #         summary = json.loads(res)
        #         return summary["summary"]
        #     except:
        #         continue
    
    def _run(
            self, query: str, _:Optional[AsyncCallbackManagerForToolRun] = None
    ):
        # res = self.llm.invoke(f"As a language expert, please summary the given text: {query}. Return the result in format:").strip()
        while True:
            try:
                res = self.llm.invoke(prompt % query)
                summary = json.loads(res)
                return summary["summary"]
            except:
                continue

prompt = """
    <|begin_of_text|><|start_header_id|>user<|end_header_id|>
    As a language expert, please summary the given text: %s. Return the result in below format without any other text:
    {
        "summary":  summary of the text
    }
    <|start_header_id|>assistant<|end_header_id|>c:w

"""