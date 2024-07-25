import os
import json
from typing import List
from langchain.agents import AgentExecutor, create_react_agent
from langchain_openai import ChatOpenAI, OpenAI
from langchain_core.prompts import PromptTemplate
from agent.summary_tool import SummaryTool
from agent.revisit_tool import SummaryRevisitTool

class RevisitAgent:
    def __init__(self):
        OPENAI_API_KEY = os.getenv('LEPTON_API_KEY')
        LEPTON_API_BASE = os.getenv('LEPTON_API_BASE')
        llm = OpenAI(api_key=OPENAI_API_KEY, base_url=LEPTON_API_BASE, model="llama3-8b")
        prompt = PromptTemplate.from_template(template)
        tools = [SummaryTool(llm=llm), SummaryRevisitTool(llm=llm)]
        agent = create_react_agent(llm, tools, prompt)

        self.agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True, handle_parsing_errors=True)
    

    def invoke(self, text: str, domains: List[str]) -> str:
        while True:
            res = self.agent_executor.invoke({"text": text, "domains": ",".join(domains)})["output"]
            if "[" in res and "]" in res:
                start_index = res.find("[")
                end_index = res.rfind("]")
                return json.dumps(json.loads(res[start_index:end_index+1]), indent=2)
        



template = """

Answer the following questions as best you can. You have access to the following tools: {tools}

Given the list of domains, please help me to figure out the domains that are related to the given text.
Please only keep the domains that are related in the final answer. Note a domain is related only if the content of the text has more than 25% on
domain's topic. Do not try to make up any new domains not in the list

Use the following format:

Question: the input question you must answer

Thought: you should always think about what to do

Action: the action to take, should be one of [{tool_names}], pass text from human when using `summary` tool. Pass {{"domain": {{a domain from list given by human}}, "text": {{text}}}} when using `summary_revisit`

Action Input: the input to the action

Observation: the result of the action

... (this Thought/Action/Action Input/Observation can repeat N times)

Thought: I now know the final answer

Final Answer: the final answer to the original input question.

Make sure you're following the process of:
Step 1. Summary the original text with summary tool
Step 2. Go through each domain from domains, and ask if the domain is related to text with summary_revisit tool. If the domain is related, keep in final answer, otherwise discard it. Do not go through same domain twice

Begin!

Human:
    Domains: {domains}
    Text: {text}

{agent_scratchpad}

"""