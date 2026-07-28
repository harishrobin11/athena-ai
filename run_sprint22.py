import asyncio
from langchain_core.messages import HumanMessage
from langchain_openai import AzureChatOpenAI
from app.services.agent_framework.graph import create_athena_runtime_graph

async def test_run():
    # Instantiates the enterprise base model configuration
    llm = AzureChatOpenAI(
        azure_deployment="athena-llm-deployment",
        api_version="2024-05-01-preview"
    )
    app = create_athena_runtime_graph(llm)
    
    test_state = {
        "messages": [HumanMessage(content="Fetch the Q3 operational report and compute variance.")],
        "tenant_id": "tenant-corp-alpha",
        "workspace_id": "ws-engineering",
        "user_id": "usr-robin-95",
        "next_step": "",
        "execution_plan": [],
        "context_metadata": {}
    }
    
    async for event in app.astream(test_state):
        print(event)

if __name__ == "__main__":
    asyncio.run(test_run())