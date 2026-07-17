"""
Athena AI - Core Chat Orchestration Service
Module: app.services.chat_service
Description: Coordinates high-level transactional streaming session state, 
             manages follow-up contextual image binding, semantic memory loops,
             and bridges conversational tokens directly to agent execution runtimes.
"""

import uuid
from typing import List, Dict, Any, Optional

# Core Retrieval & System Prompt Configurations
from ..rag.retriever import Retriever
from ..rag.prompt_builder import PromptBuilder
from ..core.prompts import SYSTEM_PROMPT_TEMPLATE

# Media Asset Frameworks
from ..utils.image_storage import ImageStorage

# Long-term Semantic Ephemeral Memory Storage Hooks
from app.memory.extractor import extract_memories
from app.memory.store import save_memories, search_memories

# Core Generation Engine Architecture Interfacing Protocols
from ..providers.ollama_provider import ask_llm, stream_llm
from app.core.cancellation import create_generation, is_cancelled, cleanup_generation

# Downstream Runtime Agent Processing Blocks
from ..agents.agent_executor import run_agent, run_agent_stream

# Shared Application Local Storage Engines
from ..memory.database import (
    init_db,
    create_conversation,
    save_message,
    load_history,
)
from openai import OpenAI
from app.core.config import settings

# Secure initialization using centralized Pydantic settings
client = OpenAI(api_key=settings.OPENAI_API_KEY)


def generate_response(
    user: str,
    retriever: Retriever,
    conversation_id: Optional[str] = None,
    history: Optional[List[Dict[str, Any]]] = None,
    selected_documents: Optional[List[str]] = None,
    user_id: Optional[int] = None,
    image_path: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Evaluates a synchronous user interaction frame by binding contextual RAG metrics,
    historical metadata arrays, and runtime visual structures into the agent context loop.
    """
    print("======== BACKEND RECONSTRUCTING HISTORY MAP ========")
    
    # Reuse the latest uploaded image frame context if no new target is explicitly supplied
    if image_path is None and conversation_id:
        image_path = ImageStorage.latest_image(conversation_id)    

    if history:
        print(f"[MEMORY LOG] Synchronous history layer captured: {len(history)} items.")
        
    # Retrieve Semantic Memories
    semantic_memories = search_memories(user_id=str(user_id) if user_id else "UNKNOWN", query=user)
    if semantic_memories:
        print(f"[MEMORY LOG] Retrieved semantic memories: {semantic_memories}")
        # Inject memories as system context directly into history (if supported by agent)
        # or append it to the user query temporarily for the agent to consider.
        memory_context = "\n[Semantic Memory Context]:\n" + "\n".join(semantic_memories)
        user = user + memory_context
    
    # Route context definitions directly into your unified downstream execution agent
    answer = run_agent(
        user_query=user,
        user_id=user_id,
        selected_documents=selected_documents,
        image_path=image_path,
        history=history,  # <-- CRITICAL SPRINT 20 COMPLETENESS RECALL BINDING
    )
    
    # Perform background asynchronous extraction routines for semantic profile memory storage
    try:
        import threading
        def run_extract():
            try:
                memories = extract_memories(user)
                if memories:
                    save_memories(user_id=user_id, memories=memories)
                    print("Saved semantic memories in background:", memories)
            except Exception as ex:
                print("[MEMORY WARNING] Long-term semantic profile pipeline failed extraction:", ex)
        threading.Thread(target=run_extract, daemon=True).start()
    except Exception as e:
        print("[MEMORY WARNING] Failed to start extraction thread:", e)

    return {
        "answer": answer,
        "sources": [],
    }
    

async def generate_response_stream(
    user: str,
    retriever: Retriever,
    conversation_id: str,
    history: Optional[List[Dict[str, Any]]] = None,
    selected_documents: Optional[List[str]] = None,
    user_id: Optional[int] = None,
    image_path: Optional[str] = None,
):
    """
    Unified high-throughput streaming orchestrator emitting generation IDs and 
    real-time text chunks while tracking cancellations and handling final state validation.
    """
    # Reuse the latest uploaded image block context if this is an established thread continuation
    if image_path is None and conversation_id:
        image_path = ImageStorage.latest_image(conversation_id)    
        
    # NOTE: User input message registration is handled explicitly inside the API gateway 
    # framework routes layer to ensure strict transactional sequencing.

    from app.services.agent_framework.graph import compiled_graph
    from app.services.agent_framework.state import AthenaAgentState
    from langchain_core.messages import HumanMessage, AIMessage

    messages = []
    if history:
        for h in history:
            if h["role"] == "user":
                messages.append(HumanMessage(content=h["content"]))
            elif h["role"] == "assistant":
                messages.append(AIMessage(content=h["content"]))
    messages.append(HumanMessage(content=user))

    context_meta = {"dept_id": "GENERAL"}
    if selected_documents:
        context_meta["selected_documents"] = selected_documents

    # Retrieve Semantic Memories
    semantic_memories = search_memories(user_id=str(user_id) if user_id else "UNKNOWN", query=user)
    if semantic_memories:
        print(f"[MEMORY LOG] Retrieved semantic memories for stream: {semantic_memories}")
        context_meta["semantic_memories"] = semantic_memories

    # Optimize latency: Route simple chat queries directly to final_synthesis, bypassing supervisor orchestration
    is_simple_query = not (
        selected_documents or 
        any(k in user.lower() for k in ["search", "find", "document", "pdf", "file", "ingest", "read", "vault", "memory", "past", "remember", "earlier", "talk about"])
    )
    
    state = AthenaAgentState(
        messages=messages,
        tenant_id="default",
        workspace_id="default",
        user_id=str(user_id) if user_id else "UNKNOWN",
        next_step="final_synthesis" if is_simple_query else "supervisor",
        execution_plan=[],
        context_metadata=context_meta,
        department_boundary="GENERAL"
    )
    
    stream = compiled_graph.astream_events(state, {"recursion_limit": 15}, version="v2")

    generation_id = str(uuid.uuid4())
    print("BACKEND CREATED TRACKING GENERATION ID =", generation_id)
    create_generation(generation_id)

    # Stream the initialization tracking sequence header right to the frontend handler
    yield f"__GENERATION_ID__:{generation_id}\n"

    try:
        full_answer = ""
        try:
            async for event in stream:
                if is_cancelled(generation_id):
                    print(f"[STREAM LOG] Active interruption command fired. Purging session: {generation_id}")
                    yield "\n\n[Generation Cancelled]"
                    break
                
                if event["event"] == "on_chat_model_stream":
                    # Only stream the tokens generated by the final synthesis node (hide supervisor JSON reasoning)
                    if event.get("metadata", {}).get("langgraph_node") == "final_synthesis":
                        chunk_content = event["data"]["chunk"].content
                        if chunk_content and isinstance(chunk_content, str):
                            full_answer += chunk_content
                            yield chunk_content
        except Exception as e:
            error_msg = f"\n\n[System Error]: Agent execution crashed unexpectedly. ({str(e)})"
            full_answer += error_msg
            yield error_msg

    finally:
        # Commit the assistant's complete generated response blocks back to the database history
        if conversation_id and full_answer.strip():
            save_message(conversation_id, "assistant", full_answer)

        # Trigger background profile extraction checks for permanent knowledge management
        try:
            import threading
            def run_extract_stream():
                try:
                    memories = extract_memories(user)
                    if memories:
                        save_memories(user_id=user_id, memories=memories)
                        print("Saved background semantic profile items:", memories)
                except Exception as ex:
                    print("[MEMORY WARNING] Background memory task skipped execution:", ex)
            threading.Thread(target=run_extract_stream, daemon=True).start()
        except Exception as e:
            print("[MEMORY WARNING] Failed to start background extraction thread:", e)
            import traceback
            traceback.print_exc()

        yield "__END__"
        cleanup_generation(generation_id)
        

def chat():
    """
    Local Diagnostic CLI Interface. 
    Maintains a development sandbox loop for quick local terminal profiling.
    """
    init_db()
    conversation_id = create_conversation()
    retriever_instance = Retriever()

    print("====================================================")
    print("Athena AI — Local CLI Sandbox Environment Booted")
    print("Type 'exit' to terminate current thread context.\n")
    print("====================================================")

    while True:
        try:
            user_input = input("You: ")
            if user_input.lower() == "exit":
                print("Athena: Disconnecting sandbox session safely. Goodbye!")
                break

            if not user_input.strip():
                continue

            save_message(conversation_id, "user", user_input)
            
            # Reconstruct the historical log array from local memory registers
            history_rows = load_history(conversation_id)
            
            # Standardize structural properties to match service specifications
            formatted_history = [{"role": row[0], "content": row[1]} for row in history_rows]

            result = generate_response(
                user=user_input,
                retriever=retriever_instance,
                conversation_id=conversation_id,
                history=formatted_history,
            )

            assistant_answer = result["answer"]
            save_message(conversation_id, "assistant", assistant_answer)

            print("\nAthena:")
            print(assistant_answer)
            print()
            
        except (KeyboardInterrupt, EOFError):
            print("\nAthena: Sandbox interrupted. Goodbye!")
            break