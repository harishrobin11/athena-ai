import json
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage
from app.schemas.agent import AgentChatRequest, AgentStreamPayload, AgentEventType
from app.services.agent_framework.graph import compiled_graph

router = APIRouter(prefix="/agent", tags=["agent"])

async def get_current_department(token: str = "mock-token") -> str:
    return "FINANCE"

@router.post("/chat")
async def agent_chat(
    payload: AgentChatRequest,
    department: str = Depends(get_current_department)
):
    initial_state = {
        "messages": [HumanMessage(content=payload.message)],
        "department_boundary": department,
        "execution_plan": [],
        "next_step": "supervisor",
        "tenant_id": payload.tenant_id,
        "workspace_id": payload.workspace_id,
        "user_id": "api_user",
        "context_metadata": {"dept_id": department, "workspace_id": payload.workspace_id}
    }

    import uuid
    async def event_generator():
        try:
            unique_thread_id = str(uuid.uuid4())
            config = {"configurable": {"thread_id": unique_thread_id}}
            # Run the compiled multi-agent asynchronous graph loop stream
            async for chunk in compiled_graph.astream(initial_state, config=config, stream_mode="updates"):
                for node_name, node_output in chunk.items():
                    if "messages" in node_output and node_output["messages"]:
                        last_msg = node_output["messages"][-1]
                        content = getattr(last_msg, "content", str(last_msg))
                        
                        if node_name == "final_synthesis":
                            payload_dict = AgentStreamPayload(
                                event_type=AgentEventType.TOKEN, 
                                node_name=node_name, 
                                content=content
                            ).model_dump()
                            yield f"data: {json.dumps(payload_dict)}\n\n"
                        else:
                            payload_dict = AgentStreamPayload(
                                event_type=AgentEventType.THOUGHT, 
                                node_name=node_name, 
                                content=content
                            ).model_dump()
                            yield f"data: {json.dumps(payload_dict)}\n\n"

                    
                    payload_dict = AgentStreamPayload(
                        event_type=AgentEventType.NODE_END, 
                        node_name=node_name, 
                        content=""
                    ).model_dump()
                    yield f"data: {json.dumps(payload_dict)}\n\n"

            payload_dict = AgentStreamPayload(
                event_type=AgentEventType.FINAL_RESPONSE,
                node_name="Orchestrator",
                content="Graph loop workflow reached completion status.",
                metadata={"sources": ["finance_policy_2026.pdf", "compliance_audit_v4.db"]}
            ).model_dump()
            yield f"data: {json.dumps(payload_dict)}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")