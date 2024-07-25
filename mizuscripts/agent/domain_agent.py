import os
import json
from langchain.agents import AgentExecutor, create_react_agent
from langchain_openai import ChatOpenAI, OpenAI
from langchain_core.prompts import PromptTemplate
from agent.summary_tool import SummaryTool
from agent.revisit_tool import SummaryRevisitTool
from utils import chunk
from typing import List

class DomainAgent:
    MAXIMAL_CONTEXT_SIZE = 1024 * 5
    BUFFER_SIZE = 500

    def __init__(self, llm):
        prompt = PromptTemplate.from_template(template)
        self.summary_tool = SummaryTool(llm=llm)
        tools = [self.summary_tool]
        agent = create_react_agent(llm, tools, prompt)

        self.llm = llm
        self.agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True, handle_parsing_errors=True)

    def invoke(self, text: str) -> List[str]:
        while True:
            # res = self.agent_executor.invoke({"text": text})["output"]
            res = self.llm.invoke(short_promopt % text)
            if "[" in res and "]" in res:
                start_index = res.find("[")
                end_index = res.rfind("]")
                return json.loads(res[start_index:end_index+1])
        

short_promopt = """
    <|begin_of_text|><|start_header_id|>user<|end_header_id|>
    As a language expert, please figure out domains from the given text: %s. Return the result in below format without any other text:
    [ 
        "domain name 1",
        "domain name 2",
        ...
    ]
    <|start_header_id|>assistant<|end_header_id|>c:w

"""


template = """

Answer the following questions as best you can. You have access to the following tools: {tools}

Please help me to figure out a list of domains for the given text. In order to find the 
related domains, please try to summarize what the text given is first. A domain should have a single meaning, try
to avoid A and B format when summarizing the domain name. Before we get the final answer, make sure you revist the 
list of domains you get and see if that's related to the original text.


To use a tool, please use the following format:

```

Thought: Do I need to use a tool? Yes

Action: the action to take, should be one of [{tool_names}]

Action Input: the input to the action, pass the text given by user when using summary tool

Observation: the result of the action

```

When you have a response to say to the Human, or if you do not need to use a tool, you MUST use the format:

```

Thought: Do I need to use a tool? No

Final Answer: Final answer in below json format:
[
    "domain name 1",
    "domain name 2",
    ...
]

```


Make sure you're following the process of:
Step 1. Summary the original text
Step 2. Figure out domains

Begin!

Human: {text}

{agent_scratchpad}

"""