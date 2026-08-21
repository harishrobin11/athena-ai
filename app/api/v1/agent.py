import json
import re
import uuid
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage
from app.schemas.agent import AgentChatRequest, AgentStreamPayload, AgentEventType
from app.services.agent_framework.graph import compiled_graph

router = APIRouter(prefix="/agent", tags=["agent"])

async def get_current_department(token: str = "mock-token") -> str:
    return "FINANCE"


# ─── Intent Classification Helpers ──────────────────────────────────────────────

GREETING_PHRASES = {
    "hi", "hello", "hey", "hi athena", "hello athena", "good morning",
    "good afternoon", "good evening", "greetings", "hey athena", "yo", "howdy",
}

# Keywords that strongly indicate a document/PDF query
DOC_KEYWORDS = {
    "pdf", "document", "file", "uploaded", "invoice", "summarize", "summary",
    "notes", "extract", "read my", "parse", "uploaded file",
}

# Keywords that indicate the user wants a diagram
DIAGRAM_KEYWORDS = {
    "diagram", "flowchart", "architecture", "ascii", "draw", "visualize",
    "sequence diagram", "uml", "box diagram", "mermaid", "flow chart",
    "visual breakdown", "schematic",
}

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp", ".tiff"}
PDF_EXTENSIONS = {".pdf"}


def classify_intent(msg_text: str, selected_docs: list[str]) -> str:
    """
    Classifies user intent into a routing target:
      - "greeting"        → hardcoded fast-path
      - "rag_worker"      → PDF/document RAG retrieval
      - "document_worker" → image vision analysis
      - "final_synthesis" → general LLM (skip supervisor entirely)
      - "supervisor"      → complex multi-step (fallback)
    """
    clean = re.sub(r'[^\w\s]', '', msg_text).strip().lower()

    # 1. Pure greetings
    if clean in GREETING_PHRASES:
        return "greeting"

    # 2. Check attachment types
    has_image = any(
        any(doc.lower().endswith(ext) for ext in IMAGE_EXTENSIONS)
        for doc in selected_docs
    )
    has_pdf = any(
        any(doc.lower().endswith(ext) for ext in PDF_EXTENSIONS)
        for doc in selected_docs
    )

    # Image attached → vision analysis
    if has_image:
        return "document_worker"

    # PDF attached → RAG retrieval
    if has_pdf:
        return "rag_worker"

    # 3. Document keywords without attachment → still route to RAG
    if any(kw in clean for kw in DOC_KEYWORDS):
        return "rag_worker"

    # 4. Diagram requests → let final_synthesis handle with ASCII art prompt
    if any(kw in clean for kw in DIAGRAM_KEYWORDS):
        return "final_synthesis"

    # 5. Complex multi-step queries that need supervisor orchestration
    complex_keywords = {"sql", "database", "query table", "automate", "schedule", "cron",
                        "search the web", "google", "internet", "news", "latest",
                        "generate image", "create image", "workflow"}
    if any(kw in clean for kw in complex_keywords):
        return "supervisor"

    # 6. Default: General knowledge / conversation → direct to LLM
    return "final_synthesis"


@router.post("/chat")
async def agent_chat(
    payload: AgentChatRequest,
    department: str = Depends(get_current_department)
):
    msg_text = (payload.message or "").strip().lower()
    selected_docs = payload.selected_documents or []

    intent = classify_intent(msg_text, selected_docs)
    print(f"[AGENT ROUTER] Intent: {intent} | Query: {msg_text[:80]} | Docs: {selected_docs}")

    async def event_generator():
        try:
            import asyncio

            # ─── Fast Path: Greetings ────────────────────────────────────────
            if intent == "greeting" and not selected_docs:
                greeting_response = (
                    f"Hello! I am your Athena AI assistant for the {department} department. "
                    f"How can I assist you with your queries today?"
                )
                words = greeting_response.split(" ")
                accum_text = ""
                for w in words:
                    word_chunk = w + " "
                    payload_dict = AgentStreamPayload(
                        event_type=AgentEventType.TOKEN,
                        node_name="final_synthesis",
                        content=word_chunk
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

            # ─── Graph Execution with Smart Entry Point ──────────────────────
            initial_state = {
                "messages": [HumanMessage(content=payload.message)],
                "department_boundary": department,
                "execution_plan": [],
                "next_step": intent,  # KEY FIX: Pre-route based on intent
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
            accumulated_tokens = ""
            final_synthesis_text = ""

            async for event in compiled_graph.astream_events(initial_state, config=config, version="v2"):
                event_type_name = event.get("event", "")
                metadata = event.get("metadata", {})
                node_name = metadata.get("langgraph_node", "")

                # ⚡️ Stream individual tokens instantly as they are generated by the LLM
                if event_type_name == "on_chat_model_stream" and node_name == "final_synthesis":
                    chunk = event.get("data", {}).get("chunk")
                    chunk_text = getattr(chunk, "content", "") if chunk else ""
                    if chunk_text and isinstance(chunk_text, str):
                        accumulated_tokens += chunk_text
                        payload_dict = AgentStreamPayload(
                            event_type=AgentEventType.TOKEN,
                            node_name="final_synthesis",
                            content=chunk_text  # Send ONLY the delta chunk text!
                        ).model_dump()
                        yield f"data: {json.dumps(payload_dict)}\n\n"

                elif event_type_name == "on_chain_end" and node_name in ["final_synthesis", "rag_worker", "document_worker"]:
                    output = event.get("data", {}).get("output", {})
                    if isinstance(output, dict) and "messages" in output and output["messages"]:
                        last_msg = output["messages"][-1]
                        msg_content = getattr(last_msg, "content", str(last_msg))
                        if msg_content and "[Worker Result]" not in msg_content:
                            final_synthesis_text = msg_content
                        elif msg_content and not final_synthesis_text:
                            final_synthesis_text = msg_content

                elif event_type_name == "on_chain_start" and node_name and node_name not in ["LangGraph", "compiled_graph"]:
                    payload_dict = AgentStreamPayload(
                        event_type=AgentEventType.THOUGHT,
                        node_name=node_name,
                        content=f"Analyzing ({node_name.replace('_', ' ')})..."
                    ).model_dump()
                    yield f"data: {json.dumps(payload_dict)}\n\n"

            final_output_content = (accumulated_tokens or final_synthesis_text).strip()
            if not final_output_content:
                final_output_content = "I processed your request but couldn't generate a response. Please try again."

            payload_dict = AgentStreamPayload(
                event_type=AgentEventType.FINAL_RESPONSE,
                node_name="Orchestrator",
                content=final_output_content,
                metadata={}
            ).model_dump()
            yield f"data: {json.dumps(payload_dict)}\n\n"

        except Exception as e:
            print(f"[AGENT ERROR] {e}")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")