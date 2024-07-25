import os
from openai import AsyncOpenAI

OPENAI_API_KEY = os.getenv('LEPTON_API_KEY')
LEPTON_API_BASE = os.getenv('LEPTON_API_BASE')

async def ainvoke(_: AsyncOpenAI, query: str):
    llm = AsyncOpenAI(api_key=OPENAI_API_KEY, base_url=LEPTON_API_BASE) #, model="llama3-8b", verbose=False)
    completion = await llm.chat.completions.create(
        model="llama-3-7b",
        messages = [
            {"role": "user", "content": query}
        ],
        temperature=0,
    )
    return completion.choices[0].message.content