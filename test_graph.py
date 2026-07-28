import asyncio
import os
import sys
from pathlib import Path

sys.path.append(str(Path.cwd()))
from app.services.agent_framework.graph import compiled_graph
from app.services.agent_framework.state import AthenaAgentState
from langchain_core.messages import HumanMessage, AIMessage

async def main():
    state = AthenaAgentState(
        messages=[HumanMessage(content="Hello world!")],
        tenant_id="default",
        workspace_id="default",
        user_id="UNKNOWN",
        next_step="supervisor",
        execution_plan=[],
        context_metadata={"dept_id": "GENERAL"},
        department_boundary="GENERAL"
    )
    
    print("Starting graph stream...")
    try:
        async for chunk in compiled_graph.astream(state):
            print("CHUNK:", chunk)
    except Exception as e:
        print("ERROR:", str(e))

if __name__ == "__main__":
    asyncio.run(main())
