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
    msg_text = (payload.message or "").strip().lower()
    selected_docs = payload.selected_documents or []
    
    # Ultra-Fast Path for casual greetings & direct chat turns
    is_simple_greeting = any(kw in msg_text for kw in ["hi", "hello", "hey", "hi athena", "hello athena", "good morning", "good afternoon"]) and len(msg_text.split()) <= 4

    import uuid
    async def event_generator():
        try:
            from app.services.agent_framework.supervisor import azure_llm
            from langchain_core.messages import SystemMessage, HumanMessage

            if is_simple_greeting and not selected_docs:
                greeting_response = f"Hello! I am Athena AI, your Enterprise Knowledge Assistant for the {department} department. How can I assist you with your documents or queries today?"
                words = greeting_response.split(" ")
                accum_text = ""
                import asyncio
                for w in words:
                    accum_text += (w + " ")
                    payload_dict = AgentStreamPayload(
                        event_type=AgentEventType.TOKEN,
                        node_name="final_synthesis",
                        content=accum_text.strip()
                    ).model_dump()
                    yield f"data: {json.dumps(payload_dict)}\n\n"
                    await asyncio.sleep(0.03)

                payload_dict = AgentStreamPayload(
                    event_type=AgentEventType.FINAL_RESPONSE,
                    node_name="Orchestrator",
                    content="Greeting completed.",
                    metadata={}
                ).model_dump()
                yield f"data: {json.dumps(payload_dict)}\n\n"
                return


            initial_state = {
                "messages": [HumanMessage(content=payload.message)],
                "department_boundary": department,
                "execution_plan": [],
                "next_step": "supervisor",
                "tenant_id": payload.tenant_id,
                "workspace_id": payload.workspace_id,
                "user_id": 1,
                "context_metadata": {
                    "dept_id": department, 
                    "workspace_id": payload.workspace_id,
                    "selected_documents": selected_docs
                }
            }

            unique_thread_id = str(uuid.uuid4())
            config = {"configurable": {"thread_id": unique_thread_id}}
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