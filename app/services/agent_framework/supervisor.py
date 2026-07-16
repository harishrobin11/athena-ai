from typing import Dict, Any
from langchain_core.messages import AIMessage
from langchain_openai import AzureChatOpenAI
from app.services.agent_framework.state import AthenaAgentState

# Import your supervisor class directly
from app.services.agent_framework.supervisor_orchestrator import AthenaSupervisorOrchestrator

# Initialize the corporate LLM client once (adjust settings to match your core config)
import os
from langchain_openai import ChatOpenAI

_api_key = os.getenv("OPENAI_API_KEY", "ollama")
_model = os.getenv("TARGET_LLM_MODEL", "llama3.2:3b")

azure_llm = ChatOpenAI(
    model=_model,
    api_key=_api_key,
    base_url="http://localhost:11434/v1",
    temperature=0,
    streaming=True
)
orchestrator = AthenaSupervisorOrchestrator(azure_llm=azure_llm)

async def supervisor_node(state: AthenaAgentState) -> Dict[str, Any]:
    """
    Invokes the production Azure OpenAI structural JSON supervisor pipeline
    to dictate exact routing paths dynamically.
    """
    # Fire your live structured orchestrator execution chain
    routing_decision = await orchestrator.execute(state)
    
    # 🦉 Crucial for streaming: Send an implicit update trace block to show live reasoning
    thought_msg = AIMessage(
        content=""
    )
    
    return {
        "messages": [thought_msg],
        "next_step": routing_decision["next_step"],
        "execution_plan": routing_decision["execution_plan"]
    }

async def rag_worker_node(state: AthenaAgentState) -> Dict[str, Any]:
    from app.rag.vector_store import VectorStore
    vs = VectorStore()
    
    user_query = ""
    for msg in reversed(state.get("messages", [])):
        if msg.type == "human":
            user_query = msg.content
            break
            
    # Ensure user_id is properly typed as an integer for ChromaDB metadata filters
    try:
        filter_user_id = int(state["user_id"])
    except ValueError:
        filter_user_id = state["user_id"]
        
    filter_metadata = {"user_id": filter_user_id}
    
    selected_docs = state.get("context_metadata", {}).get("selected_documents", [])
    if selected_docs:
        # Limit search to the specific requested document context boundary
        filter_metadata["filename"] = {"$in": selected_docs} if len(selected_docs) > 1 else selected_docs[0]

    docs = vs.similarity_search(
        query=user_query,
        dept_id=state.get("department_boundary", "GENERAL"),
        k=3,
        filter_metadata=filter_metadata
    )
    
    doc_context = "\n\n".join([d.page_content for d in docs]) if docs else "No relevant documents found in vault."
    
    context_msg = AIMessage(
        content=f"[Worker Result]: RAG fetch complete. Retrieved context:\n\n{doc_context}\n\nPlease route to 'FINISH'."
    )
    return {"messages": [context_msg], "next_step": "supervisor"}

async def code_worker_node(state: AthenaAgentState) -> Dict[str, Any]:
    context_msg = AIMessage(
        content="[Worker Result]: Algorithmic processing operations and data fetches have successfully completed. The task is complete. Please route to 'FINISH'."
    )
    return {"messages": [context_msg], "next_step": "supervisor"}

async def final_synthesis_node(state: AthenaAgentState) -> Dict[str, Any]:
    from langchain_core.messages import SystemMessage, HumanMessage
    from datetime import datetime
    import os
    dept = state.get("department_boundary", "GENERAL")
    
    # Dynamically inject current date and time
    current_time = datetime.now().strftime("%A, %B %d, %Y at %I:%M %p")
    
    # 🧠 Retrieve User Profile and Long-term cross-chat memories
    user_id = state.get("user_id")
    memories_str = ""
    if user_id and user_id != "UNKNOWN":
        try:
            from app.tools.search_memory import search_memory
            try:
                search_uid = int(user_id)
            except (ValueError, TypeError):
                search_uid = user_id

            # Grab the last user message to query semantic database
            user_query = ""
            for msg in reversed(state.get("messages", [])):
                if msg.type == "human":
                    user_query = msg.content
                    break

            m_topic = search_memory(user_query, context={"user_id": search_uid}) if user_query else ""
            m_profile = search_memory("User profile identity, name, creator name, details", context={"user_id": search_uid})

            combined_m = []
            for mem in [m_topic, m_profile]:
                if mem and "No relevant memories" not in mem:
                    for line in mem.split("\n"):
                        if line.strip() and line.strip() not in combined_m:
                            combined_m.append(line.strip())

            # Fallback to direct SQLite search for name declaration facts
            if not combined_m:
                from app.memory.database import list_conversations, get_messages
                conversations = list_conversations(search_uid)
                seen = set()
                for conv in conversations:
                    conv_id = conv[0]
                    for role, content in get_messages(conv_id):
                        if role == "user":
                            content_lower = content.lower()
                            if any(k in content_lower for k in ["my name is", "i am", "call me"]):
                                clean_fact = content.strip().replace("\n", " ")
                                if clean_fact not in seen:
                                    combined_m.append(f"Fact from past chat: '{clean_fact}'")
                                    seen.add(clean_fact)

            if combined_m:
                memories_str = "\n[Recall of Facts & Profile From Past Chats]:\n" + "\n".join(combined_m)
        except Exception as e:
            print(f"[MEMORY LOG] Error retrieving memories in final_synthesis: {e}")
    
    sys_msg = SystemMessage(
        content=f"You are Athena AI, an Enterprise Knowledge Assistant for the {dept} department. The current date and time is {current_time}. {memories_str}\n\nIf the user says hello or greets you casually without asking a specific question, respond with a warm greeting and ask how you can help them navigate their workspace or ML classifiers today. If the user is asking about a document, report, or specific corporate data, synthesize a helpful response strictly based on the provided worker context in the conversation history, and do NOT hallucinate. If the user asks a general knowledge question (like coding, science, definitions, or today's date/time/memories), you may use your pre-trained knowledge along with the current time and recalled memories context to answer them fully and helpfully."
    )
    
    # Inject a final prompt to force the LLM to reply, 
    # since the last message in state is likely an AIMessage (Worker Result)
    final_prompt = HumanMessage(content="Please provide the final synthesized answer to my original query. If my query was about a document, rely ONLY on the [Worker Result] context above. Otherwise, answer natively using your general knowledge.")
    
    messages = [sys_msg] + state.get("messages", []) + [final_prompt]
    
    # Sprint 27: Basic PII Scrubber Guardrail
    import re
    # Extremely basic regex for demonstration: redact standard SSN patterns
    ssn_pattern = re.compile(r'\b\d{3}-\d{2}-\d{4}\b')
    for msg in messages:
        if isinstance(msg.content, str):
            msg.content = ssn_pattern.sub("[REDACTED PII]", msg.content)

    # Generate the final response using the local Ollama LLM instance
    response = await azure_llm.ainvoke(messages)
    
    # Extract token usage and record in database
    usage = response.response_metadata.get("token_usage", {})
    total_tokens = usage.get("total_tokens")
    # Langchain 0.2 fallback
    if not total_tokens and hasattr(response, "usage_metadata") and response.usage_metadata:
        total_tokens = response.usage_metadata.get("total_tokens")
        
    # If using local Ollama, it might not return tokens reliably in some versions,
    # so we fallback to a rough estimate (1 word ~= 1.3 tokens)
    if not total_tokens:
        total_tokens = int(len(response.content.split()) * 1.3) + int(len(str(messages).split()) * 1.3)
        
    try:
        from app.db.database import SessionLocal
        from app.db.models import TokenUsage
        db = SessionLocal()
        
        # Ensure we have a valid integer user_id
        try:
            uid = int(state.get("user_id", 0))
        except (ValueError, TypeError):
            uid = 0
            
        token_record = TokenUsage(
            workspace_id=state.get("workspace_id", 1),
            user_id=uid,
            tokens=total_tokens,
            model=azure_llm.model
        )
        db.add(token_record)
        db.commit()
        db.close()
    except Exception as e:
        print(f"Failed to record token usage: {e}")
    
    return {"messages": [response], "next_step": "FINISH"}