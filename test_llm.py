import asyncio
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

async def main():
    llm = ChatOpenAI(
        model="llama3.2:3b",
        api_key="ollama",
        base_url="http://localhost:11434/v1",
        temperature=0
    )
    messages = [
        SystemMessage(content="You are a helpful AI."),
        HumanMessage(content="what is leave?"),
        AIMessage(content="[Worker Result]: Algorithmic processing operations and data fetches have successfully completed. The task is complete. Please route to 'FINISH'."),
    ]
    res = await llm.ainvoke(messages)
    print("RESPONSE:", repr(res.content))

asyncio.run(main())
