from typing import Dict, Any
from langchain_core.messages import AIMessage
from langchain_openai import AzureChatOpenAI
from app.services.agent_framework.state import AthenaAgentState

# Import your supervisor class directly
from app.services.agent_framework.supervisor_orchestrator import AthenaSupervisorOrchestrator

# Initialize the corporate LLM client once (adjust settings to match your core config)
import os
from langchain_openai import ChatOpenAI, AzureChatOpenAI

_api_key = os.getenv("OPENAI_API_KEY", "ollama")
_model = os.getenv("TARGET_LLM_MODEL", "llama3.2:1b")

_azure_api_key = os.getenv("AZURE_OPENAI_API_KEY")
_azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
_azure_deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", _model)
_azure_api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")

if _azure_api_key and _azure_endpoint:
    azure_llm = AzureChatOpenAI(
        azure_endpoint=_azure_endpoint,
        api_key=_azure_api_key,
        api_version=_azure_api_version,
        azure_deployment=_azure_deployment,
        temperature=0,
        streaming=True,
        timeout=60.0
    )
else:
    _default_ollama = "http://host.docker.internal:11434" if os.path.exists("/.dockerenv") else "http://127.0.0.1:11434"
    _ollama_host = os.getenv("OLLAMA_HOST", _default_ollama)
    azure_llm = ChatOpenAI(
        model=_model,
        api_key=_api_key,
        base_url=f"{_ollama_host}/v1",
        temperature=0,
        streaming=True,
        timeout=60.0,
        extra_body={
            "keep_alive": -1,
            "options": {
                "num_thread": 4,
                "num_ctx": 1024
            }
        }
    )




orchestrator = AthenaSupervisorOrchestrator(azure_llm=azure_llm)

from app.core.llm_ops import track_prompt_execution

@track_prompt_execution(prompt_version="v1.0", task_name="supervisor_routing")
async def supervisor_node(state: AthenaAgentState) -> Dict[str, Any]:
    """
    Invokes the production Azure OpenAI structural JSON supervisor pipeline
    to dictate exact routing paths dynamically.
    """
    # Fire your live structured orchestrator execution chain
    routing_decision = await orchestrator.execute(state)
    
    # Crucial for streaming: Send an implicit update trace block to show live reasoning
    thought_msg = AIMessage(
        content=""
    )
    
    return {
        "messages": [thought_msg],
        "next_step": routing_decision["next_step"],
        "execution_plan": routing_decision["execution_plan"]
    }

async def rag_worker_node(state: AthenaAgentState) -> Dict[str, Any]:
    from app.rag.retriever import Retriever
    from app.memory.conversation_vector_store import ConversationVectorStore
    from app.api.routes import document_service
    retriever = Retriever()
    conv_store = ConversationVectorStore()
    
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
    
    import os
    import glob
    from app.rag.loader import load_pdf
    from langchain_core.documents import Document

    selected_docs = state.get("context_metadata", {}).get("selected_documents", [])
    
    # Auto-discover uploaded document if not explicitly passed
    if not selected_docs:
        all_pdfs = glob.glob(os.path.join(os.getcwd(), "storage", "documents", "**", "*.pdf"), recursive=True)
        if all_pdfs:
            latest_pdf = max(all_pdfs, key=os.path.getmtime)
            selected_docs = [os.path.basename(latest_pdf)]

    docs = []

    # Instant Fast-Path 1: Check in-memory document text cache (0ms delay)
    if selected_docs:
        for doc_name in selected_docs:
            cached_text = document_service.get_cached_document_text(doc_name)
            if cached_text:
                docs.append(Document(page_content=cached_text, metadata={"filename": doc_name, "source": "in_memory_cache"}))
                print(f"[RAG WORKER] Loaded fast in-memory cache context for: {doc_name}")

    if not docs and selected_docs:
        filter_metadata = {
            "$and": [
                {"user_id": filter_user_id},
                {"filename": {"$in": selected_docs} if len(selected_docs) > 1 else selected_docs[0]}
            ]
        }

        docs = retriever.retrieve(
            query=user_query,
            dept_id=state.get("department_boundary", "GENERAL"),
            top_k=5,
            filter_metadata=filter_metadata,
            use_hybrid=True
        )
    elif not docs:
        docs = retriever.retrieve(
            query=user_query,
            dept_id=state.get("department_boundary", "GENERAL"),
            top_k=5,
            filter_metadata={"user_id": filter_user_id},
            use_hybrid=True
        )

    # Fallback 1: Try general vector retrieval without user_id filter
    if not docs:
        docs = retriever.retrieve(
            query=user_query,
            dept_id=state.get("department_boundary", "GENERAL"),
            top_k=5,
            filter_metadata=None,
            use_hybrid=True
        )

    # Fallback 2: Direct multi-path disk search & fast full-text extraction
    if not docs and selected_docs:
        target_name = selected_docs[0]
        possible_paths = [
            os.path.join(os.getcwd(), "storage", "documents", f"user_{filter_user_id}", target_name),
            os.path.join(os.getcwd(), "storage", "documents", target_name),
            os.path.join(os.getcwd(), "storage", "documents", "user_1", target_name),
            os.path.join(os.getcwd(), "storage", "documents", "user_None", target_name),
        ]
        for p in possible_paths:
            if os.path.exists(p):
                try:
                    loaded_docs = load_pdf(p)
                    if loaded_docs:
                        docs = loaded_docs
                        document_service.cache_document_text(target_name, loaded_docs, user_id=filter_user_id)
                        print(f"[RAG WORKER] Successfully loaded {len(docs)} pages from disk file: {p}")
                        break
                except Exception as ex:
                    print(f"[RAG WORKER] Direct file load failed for {p}: {ex}")

    # Fallback 3: Execute Document AI Tool Layout Parser
    if not docs and selected_docs:
        from app.tools.registry import execute_tool
        doc_analysis = execute_tool("analyze_document_layout", selected_docs[0])
        if doc_analysis and "could not be resolved" not in doc_analysis:
            docs = [Document(page_content=doc_analysis, metadata={"filename": selected_docs[0]})]

    
    # Sprint 14: Conversation Intelligence - Fetch & Rank Memory
    past_conversations = []
    try:
        conv_docs = conv_store.search_messages(query=user_query, user_id=str(state["user_id"]), k=5)
        past_conversations = conv_docs
    except Exception as e:
        print(f"[RAG WORKER] Error retrieving past conversations: {e}")
        
    doc_context = "\n\n".join([d.page_content for d in docs]) if docs else ""
    
    conv_context = "\n\n".join([
        f"[{d.metadata.get('timestamp', 'Unknown')}] {d.metadata.get('role', 'Unknown').capitalize()}: {d.page_content}" 
        for d in past_conversations
    ]) if past_conversations else ""

    if doc_context or conv_context:
        combined_context = f"[Enterprise Documents]:\n{doc_context}\n\n[Past Conversations]:\n{conv_context}".strip()
        context_msg = AIMessage(
            content=f"[Worker Result]: RAG fetch complete. Retrieved context:\n\n{combined_context}"
        )
    else:
        context_msg = AIMessage(
            content=f"[Worker Result]: No specific document matches found in knowledge vault. Proceeding with general knowledge response."
        )
    return {"messages": [context_msg], "next_step": "supervisor"}

async def code_worker_node(state: AthenaAgentState) -> Dict[str, Any]:
    from app.tools.registry import execute_tool
    from langchain_core.messages import SystemMessage, HumanMessage
    
    user_query = ""
    for msg in reversed(state.get("messages", [])):
        if msg.type == "human":
            user_query = msg.content
            break

    # 1. Generate Python code
    py_gen_prompt = SystemMessage(
        content="You are an expert Python programmer. Based on the user's request, write a self-contained Python script to solve the problem or calculate the answer. The script should `print()` the final result so it can be captured by standard output. Return ONLY the raw Python code without any markdown formatting or backticks."
    )
    py_gen_query = HumanMessage(content=user_query)
    py_code_response = await azure_llm.ainvoke([py_gen_prompt, py_gen_query])
    py_code = py_code_response.content.strip().replace("```python", "").replace("```", "").strip()

    print("[CODE WORKER] Executing Python code:\n", py_code)
    py_result = execute_tool("execute_python", py_code)
    
    # 2. Synthesize output
    sys_prompt = SystemMessage(
        content="You are the Athena Code Analyst. Synthesize the execution output of the Python script into a clear, natural language summary."
    )
    
    query_prompt = HumanMessage(
        content=f"User Query: {user_query}\n\nPython Code Executed:\n{py_code}\n\nStandard Output Trace:\n{py_result}\n\nPlease provide a clear human-readable summary of the answer."
    )
    
    response = await azure_llm.ainvoke([sys_prompt, query_prompt])
    
    context_msg = AIMessage(
        content=f"[Worker Result]: Python execution completed.\n\n{response.content}"
    )
    return {"messages": [context_msg], "next_step": "supervisor"}

async def workflow_worker_node(state: AthenaAgentState) -> Dict[str, Any]:
    from app.tools.registry import execute_tool
    from langchain_core.messages import SystemMessage, HumanMessage
    import json
    
    user_query = ""
    for msg in reversed(state.get("messages", [])):
        if msg.type == "human":
            user_query = msg.content
            break

    # 1. Determine Workflow Tasks
    wf_gen_prompt = SystemMessage(
        content="You are an expert Workflow Automation Agent. Based on the user's request, determine the necessary API calls and schedule configurations. Output a JSON object with 'api_calls' (list of dicts with url, method, payload) and 'schedule' (dict with task_name, delay/cron_expression, or null if no schedule). Return ONLY the raw JSON without markdown."
    )
    wf_gen_query = HumanMessage(content=user_query)
    wf_response = await azure_llm.ainvoke([wf_gen_prompt, wf_gen_query])
    
    try:
        wf_json_str = wf_response.content.strip().replace("```json", "").replace("```", "").strip()
        wf_plan = json.loads(wf_json_str)
    except json.JSONDecodeError:
        wf_plan = {"api_calls": [], "schedule": None}

    results = []
    
    # 2. Execute API Calls
    for api_call in wf_plan.get("api_calls", []):
        print(f"[WORKFLOW WORKER] Executing API call: {api_call}")
        res = execute_tool("execute_api", json.dumps(api_call))
        results.append(f"API Output: {res}")
        
    # 3. Schedule Task
    schedule_config = wf_plan.get("schedule")
    if schedule_config:
        print(f"[WORKFLOW WORKER] Scheduling task: {schedule_config}")
        res = execute_tool("schedule_task", json.dumps(schedule_config))
        results.append(f"Schedule Output: {res}")

    combined_results = "\n".join(results)
    
    # 4. Synthesize output
    sys_prompt = SystemMessage(
        content="You are the Athena Workflow Architect. Synthesize the execution outputs of the workflow steps into a clear, natural language summary."
    )
    
    query_prompt = HumanMessage(
        content=f"User Query: {user_query}\n\nWorkflow Output:\n{combined_results}\n\nPlease provide a clear human-readable summary of the automated actions."
    )
    
    final_response = await azure_llm.ainvoke([sys_prompt, query_prompt])
    
    context_msg = AIMessage(
        content=f"[Worker Result]: Workflow automation completed.\n\n{final_response.content}"
    )
    return {"messages": [context_msg], "next_step": "supervisor"}

async def research_worker_node(state: AthenaAgentState) -> Dict[str, Any]:
    from app.tools.registry import execute_tool
    from langchain_core.messages import SystemMessage, HumanMessage
    
    user_query = ""
    for msg in reversed(state.get("messages", [])):
        if msg.type == "human":
            user_query = msg.content
            break

    # Execute duckduckgo search
    print("[RESEARCH WORKER] Executing web search for:", user_query)
    search_result = execute_tool("web_search", user_query)
    
    sys_prompt = SystemMessage(
        content="You are the Athena Research Agent. Your job is to summarize and verify facts based on live internet search results provided below. Be concise, objective, and cite the internet findings."
    )
    
    query_prompt = HumanMessage(
        content=f"User Query: {user_query}\n\nSearch Results:\n{search_result}\n\nPlease synthesize a final summarized research report."
    )
    
    # Synthesize the findings using the LLM
    response = await azure_llm.ainvoke([sys_prompt, query_prompt])
    
    context_msg = AIMessage(
        content=f"[Worker Result]: Research completed.\n\n{response.content}"
    )
    return {"messages": [context_msg], "next_step": "supervisor"}

async def document_worker_node(state: AthenaAgentState) -> Dict[str, Any]:
    from app.tools.registry import execute_tool
    from langchain_core.messages import SystemMessage, HumanMessage
    import re
    
    user_query = ""
    for msg in reversed(state.get("messages", [])):
        if msg.type == "human":
            user_query = msg.content
            break

    selected_docs = state.get("context_metadata", {}).get("selected_documents", [])
    filename = ""

    if selected_docs and len(selected_docs) > 0:
        filename = selected_docs[0]
    else:
        # Fast regex match for file extensions
        match = re.search(r'[\w\-. ]+\.(pdf|png|jpg|jpeg|csv|txt)', user_query, re.IGNORECASE)
        if match:
            filename = match.group(0).strip()

    # Fallback to LLM extraction only if filename remains unresolved
    if not filename:
        extract_prompt = SystemMessage(
            content="Extract the exact PDF filename the user wants to analyze from the query. Return ONLY the filename (e.g. invoice.pdf). If no filename is found, return 'unknown.pdf'."
        )
        extract_query = HumanMessage(content=user_query)
        filename_response = await azure_llm.ainvoke([extract_prompt, extract_query])
        filename = filename_response.content.strip()

    print("[DOCUMENT WORKER] Processing document:", filename)

    # 🖼️ Vision AI path for Image Attachments (png, jpg, jpeg, webp)
    if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.webp', '.gif')):
        print("[DOCUMENT WORKER] Detected image file, invoking Vision AI:", filename)
        import os
        import glob
        import base64
        import ollama

        possible_paths = [
            os.path.join(os.getcwd(), "storage", "documents", f"user_1", filename),
            os.path.join(os.getcwd(), "storage", "documents", filename),
        ]
        img_path = None
        for p in possible_paths:
            if os.path.exists(p):
                img_path = p
                break
        if not img_path:
            all_imgs = glob.glob(os.path.join(os.getcwd(), "storage", "documents", "**", filename), recursive=True)
            if all_imgs:
                img_path = all_imgs[0]

        if img_path and os.path.exists(img_path):
            try:
                with open(img_path, "rb") as f:
                    img_b64 = base64.b64encode(f.read()).decode("utf-8")
                print(f"[DOCUMENT WORKER] Running Moondream vision analysis on {img_path}...")
                vision_res = ollama.chat(
                    model="moondream:latest",
                    messages=[{
                        "role": "user",
                        "content": user_query or "Describe this image in detail.",
                        "images": [img_b64]
                    }]
                )
                vision_text = vision_res.message.content if hasattr(vision_res, 'message') else str(vision_res.get("message", {}).get("content", ""))
                context_msg = AIMessage(
                    content=f"[Worker Result]: Vision Image Analysis for '{filename}':\n\n{vision_text}"
                )
                return {"messages": [context_msg], "next_step": "supervisor"}
            except Exception as ve:
                print(f"[DOCUMENT WORKER] Vision model execution failed: {ve}")

    doc_result = execute_tool("analyze_document_layout", filename)
    
    sys_prompt = SystemMessage(
        content="You are the Athena Document Agent. Your job is to synthesize raw extracted PDF layout and table data into a clean, human-readable report."
    )
    
    query_prompt = HumanMessage(
        content=f"User Query: {user_query}\n\nDocument Layout Data:\n{doc_result}\n\nPlease synthesize a final report based on this data."
    )
    
    response = await azure_llm.ainvoke([sys_prompt, query_prompt])
    
    context_msg = AIMessage(
        content=f"[Worker Result]: Document parsed.\n\n{response.content}"
    )
    return {"messages": [context_msg], "next_step": "supervisor"}

@track_prompt_execution(prompt_version="v1.0", task_name="sql_analytics")
async def sql_worker_node(state: AthenaAgentState) -> Dict[str, Any]:
    from app.tools.registry import execute_tool
    from langchain_core.messages import SystemMessage, HumanMessage
    
    user_query = ""
    for msg in reversed(state.get("messages", [])):
        if msg.type == "human":
            user_query = msg.content
            break

    db_schema = "TABLE sales(id INTEGER PRIMARY KEY, department TEXT, revenue REAL, quarter TEXT)"
    
    # 1. Generate SQL query
    sql_gen_prompt = SystemMessage(
        content=f"You are a SQL expert. Based on the user's request, write a SELECT query against the following PostgreSQL schema: {db_schema}. Return ONLY the raw SQL string without any markdown backticks or explanations."
    )
    sql_gen_query = HumanMessage(content=user_query)
    sql_query_response = await azure_llm.ainvoke([sql_gen_prompt, sql_gen_query])
    sql_query = sql_query_response.content.strip().replace("```sql", "").replace("```", "").strip()

    print("[SQL WORKER] Executing query:", sql_query)
    sql_result = execute_tool("execute_sql", sql_query)
    
    # 2. Synthesize output
    sys_prompt = SystemMessage(
        content="You are the Athena Data Analyst Agent. Synthesize the raw relational data output into a clear, analytical summary."
    )
    
    query_prompt = HumanMessage(
        content=f"User Query: {user_query}\n\nSQL Query Run: {sql_query}\n\nRaw SQL Output:\n{sql_result}\n\nPlease provide a clear human-readable summary of these metrics."
    )
    
    response = await azure_llm.ainvoke([sys_prompt, query_prompt])
    
    context_msg = AIMessage(
        content=f"[Worker Result]: Database analysis completed.\n\n{response.content}"
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
    
    combined_m = state.get("context_metadata", {}).get("semantic_memories", [])
    memories_str = ""
    
    if not combined_m and user_id and user_id != "UNKNOWN":
        try:
            # Fallback to direct PostgreSQL search for name declaration facts if no semantic memories found
            from app.memory.database import list_conversations, get_messages
            try:
                search_uid = int(user_id)
            except (ValueError, TypeError):
                search_uid = user_id

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
        except Exception as e:
            print(f"[MEMORY LOG] Error retrieving memories fallback in final_synthesis: {e}")

    if combined_m:
        memories_str = "\n[Recall of Facts & Profile From Past Chats]:\n" + "\n".join(combined_m)
    
    # Compact Prompt Construction: Extract only user query and worker results
    user_query = ""
    for msg in reversed(state.get("messages", [])):
        if getattr(msg, "type", "") == "human":
            user_query = str(msg.content)
            break

    worker_facts = []
    for msg in state.get("messages", []):
        text = str(getattr(msg, "content", ""))
        if "[Worker Result]" in text or "Retrieved context:" in text:
            clean_text = text.replace("[Worker Result]:", "").strip()
            worker_facts.append(clean_text)

    facts_context = ("\n\n[Retrieved Context & Data]:\n" + "\n".join(worker_facts)) if worker_facts else ""

    sys_msg = SystemMessage(
        content=(
            f"You are Athena AI, an intelligent Enterprise Knowledge Assistant for the {dept} department. {memories_str}\n{facts_context}\n\n"
            "Instructions:\n"
            "1. If relevant enterprise documents or worker results are provided above, prioritize them to answer the user query.\n"
            "2. If no specific enterprise documents were found in the vault, answer the user query thoroughly, accurately, and helpfully using your general AI knowledge.\n"
            "3. Do NOT state that you lack information or refuse to answer simply because a document was not uploaded, unless the user explicitly requested a specific missing file.\n"
            "4. Do not cite internal system tags, worker labels, or metadata."
        )
    )
    
    compact_messages = [sys_msg, HumanMessage(content=user_query or "Hi")]

    # Sprint 27: Basic PII Scrubber Guardrail
    import re
    ssn_pattern = re.compile(r'\b\d{3}-\d{2}-\d{4}\b')
    for msg in compact_messages:
        if isinstance(msg.content, str):
            msg.content = ssn_pattern.sub("[REDACTED PII]", msg.content)

    # Generate the final response using the LLM instance with a 25s timeout
    try:
        import asyncio
        response = await asyncio.wait_for(azure_llm.ainvoke(compact_messages), timeout=25.0)
    except Exception as e:
        print(f"[LLM FALLBACK WARNING] LLM invoke failed or timed out in final_synthesis: {e}")
        if worker_facts:
            synthesized_text = "### Athena Document & Knowledge Synthesis\n\n" + "\n\n---\n\n".join(worker_facts)
        elif facts_context:
            synthesized_text = "### Athena Knowledge Synthesis\n\n" + facts_context
        else:
            synthesized_text = "Hello! How can I assist you with your workspace tasks today?"
            
        response = AIMessage(content=synthesized_text)

    
    # Extract token usage and record in database
    usage = getattr(response, "response_metadata", {}).get("token_usage", {})
    total_tokens = usage.get("total_tokens")
    # Langchain 0.2 fallback
    if not total_tokens and hasattr(response, "usage_metadata") and response.usage_metadata:
        total_tokens = response.usage_metadata.get("total_tokens")
        
    # If using local Ollama or fallback, estimate token count
    if not total_tokens:
        total_tokens = int(len(response.content.split()) * 1.3) + int(len(str(compact_messages).split()) * 1.3)

        
    try:
        from app.db.database import SessionLocal
        from app.db.models import TokenUsage
        db = SessionLocal()
        
        try:
            uid = int(state.get("user_id", 0))
        except (ValueError, TypeError):
            uid = 0
            
        token_record = TokenUsage(
            workspace_id=state.get("workspace_id", 1),
            user_id=uid,
            tokens=total_tokens,
            model=getattr(azure_llm, "model", getattr(azure_llm, "model_name", "azure-openai"))
        )
        db.add(token_record)
        db.commit()
        db.close()
    except Exception as e:
        print(f"Failed to record token usage: {e}")
    
    return {"messages": [response], "next_step": "FINISH"}