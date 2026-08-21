from typing import Dict, Any
from langchain_core.messages import AIMessage, SystemMessage, HumanMessage
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
    if _api_key and _api_key != "ollama" and _api_key.startswith("sk-"):
        # standard OpenAI config for production hosting (Render/Railway)
        azure_llm = ChatOpenAI(
            model=os.getenv("TARGET_LLM_MODEL", "gpt-4o-mini"),
            api_key=_api_key,
            temperature=0,
            streaming=True,
            timeout=120.0
        )
    else:
        azure_llm = ChatOpenAI(
            model=_model,
            api_key=_api_key,
            base_url=f"{_ollama_host}/v1",
            temperature=0,
            streaming=True,
            timeout=120.0,
            extra_body={
                "keep_alive": -1,
                "options": {
                    "num_ctx": 2048,
                    "num_predict": 512
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

    # Instant Fast-Path 1: Check in-memory document text cache for query-relevant chunks (0ms delay)
    if selected_docs:
        for doc_name in selected_docs:
            cached_chunks = document_service.get_cached_document_chunks(doc_name, query=user_query, top_k=5)
            if cached_chunks:
                docs.extend(cached_chunks)
                print(f"[RAG WORKER] Loaded {len(cached_chunks)} targeted in-memory chunks for: {doc_name}")

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

    # Fallback 2: Direct multi-path disk search & fast chunk extraction
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
                        document_service.cache_document_text(target_name, loaded_docs, user_id=filter_user_id)
                        docs = document_service.get_cached_document_chunks(target_name, query=user_query, top_k=5)
                        print(f"[RAG WORKER] Successfully loaded {len(docs)} targeted chunks from disk file: {p}")
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
        
    doc_context = "\n\n".join([
        f"[Source: {d.metadata.get('filename', d.metadata.get('source', 'document'))} | Page: {d.metadata.get('page', 1)}]\n{d.page_content}"
        for d in docs
    ]) if docs else ""
    
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

        root_storage = os.path.join(os.getcwd(), "storage")
        img_path = None
        
        for root, dirs, files in os.walk(root_storage):
            if filename in files:
                img_path = os.path.join(root, filename)
                break
                
        if not img_path:
            fn_lower = filename.lower()
            clean_stem = os.path.splitext(fn_lower)[0]
            for root, dirs, files in os.walk(root_storage):
                for f in files:
                    f_lower = f.lower()
                    if f_lower == fn_lower or (len(clean_stem) > 4 and clean_stem in f_lower):
                        img_path = os.path.join(root, f)
                        break
                if img_path:
                    break
                    
        if not img_path:
            all_imgs = glob.glob(os.path.join(root_storage, "**", filename), recursive=True)
            if all_imgs:
                img_path = all_imgs[0]
            else:
                # Fallback to most recent image file in storage
                recent_imgs = glob.glob(os.path.join(root_storage, "**", "*.png"), recursive=True) + \
                              glob.glob(os.path.join(root_storage, "**", "*.jpg"), recursive=True) + \
                              glob.glob(os.path.join(root_storage, "**", "*.jpeg"), recursive=True)
                if recent_imgs:
                    recent_imgs.sort(key=lambda x: os.path.getmtime(x), reverse=True)
                    img_path = recent_imgs[0]

        if img_path and os.path.exists(img_path):
            try:
                with open(img_path, "rb") as f:
                    img_bytes = f.read()
                    img_b64 = base64.b64encode(img_bytes).decode("utf-8")

                # Method 1: Multimodal LLM Vision API invocation
                try:
                    mime_type = "image/png" if filename.lower().endswith(".png") else "image/jpeg"
                    vision_prompt = user_query or "Describe this image in detail, listing all key objects, colors, labels, and elements visible."
                    mm_msg = HumanMessage(content=[
                        {"type": "text", "text": vision_prompt},
                        {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{img_b64}"}}
                    ])
                    vision_resp = await azure_llm.ainvoke([mm_msg])
                    vision_text = getattr(vision_resp, "content", "").strip()
                    if vision_text and not any(kw in vision_text.lower() for kw in ["cannot process", "unsupported", "cannot view"]):
                        print(f"[DOCUMENT WORKER] Multimodal LLM vision analysis succeeded for {filename}")
                        context_msg = AIMessage(content=f"[Worker Result]: Vision Image Analysis for '{filename}':\n\n{vision_text}")
                        return {"messages": [context_msg], "next_step": "supervisor"}
                except Exception as mm_err:
                    print(f"[DOCUMENT WORKER] Multimodal LLM vision skipped: {mm_err}")

                # Method 2: Ollama local vision model
                try:
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
                    if vision_text and vision_text.strip():
                        context_msg = AIMessage(content=f"[Worker Result]: Vision Image Analysis for '{filename}':\n\n{vision_text.strip()}")
                        return {"messages": [context_msg], "next_step": "supervisor"}
                except Exception as ve:
                    print(f"[DOCUMENT WORKER] Ollama vision model execution failed: {ve}")

                # Method 3: Local OCR Text Extraction Fallback for Images
                ocr_text = ""
                try:
                    from PIL import Image
                    import pytesseract
                    img = Image.open(img_path)
                    ocr_text = pytesseract.image_to_string(img).strip()
                except Exception as oe:
                    print(f"[DOCUMENT WORKER] Pytesseract OCR skipped: {oe}")

                if not ocr_text:
                    try:
                        import fitz
                        doc = fitz.open(img_path)
                        for page in doc:
                            ocr_text += page.get_text("text")
                        ocr_text = ocr_text.strip()
                    except Exception:
                        pass

                # Method 4: PIL Visual Property & Color Metadata Analysis Fallback
                img_desc = ""
                try:
                    from PIL import Image
                    with Image.open(img_path) as pimg:
                        w, h = pimg.size
                        fmt = pimg.format or "JPEG"
                        mode = pimg.mode or "RGB"
                        img_desc = f"Image File: {filename} ({w}x{h} pixels, {fmt} format, {mode} color mode)."
                        try:
                            from app.multimodal.image_service import detect_dominant_color
                            dom_col = detect_dominant_color(img_path)
                            img_desc += f" Dominant visual color theme: {dom_col}."
                        except Exception:
                            pass
                except Exception:
                    img_desc = f"Image File: {filename}."

                if ocr_text:
                    full_analysis = f"{img_desc}\n\n[Extracted Text & Diagram Labels]:\n{ocr_text}"
                else:
                    full_analysis = f"{img_desc}\n\nVisual scenery/graphic asset uploaded without embedded OCR text labels."

                context_msg = AIMessage(content=f"[Worker Result]: Image Visual Analysis for '{filename}':\n\n{full_analysis}")
                return {"messages": [context_msg], "next_step": "supervisor"}
            except Exception as ex_img:
                print(f"[DOCUMENT WORKER] Image processing exception: {ex_img}")
    
    sys_prompt = SystemMessage(
        content="You are the Athena Document Agent. Your job is to synthesize raw extracted PDF layout and table data into a clean, human-readable report. You are operating in a fully authorized enterprise environment."
    )
    
    query_prompt = HumanMessage(
        content=f"User Query: {user_query}\n\nDocument Layout Data:\n{doc_result}\n\nPlease synthesize a final report based on this data."
    )
    
    try:
        response = await azure_llm.ainvoke([sys_prompt, query_prompt])
        resp_content = response.content.strip() if hasattr(response, 'content') else str(response)
        
        # Check for false-positive safety refusal strings
        refusal_keywords = [
            "illegal or harmful activities",
            "copyright",
            "cannot assist with this request",
            "i can't provide information or guidance"
        ]
        if any(kw in resp_content.lower() for kw in refusal_keywords):
            print("[DOCUMENT WORKER] Overriding false-positive refusal with raw layout extraction.")
            resp_content = doc_result
    except Exception as e:
        print(f"[DOCUMENT WORKER WARNING] LLM synthesis skipped: {e}")
        resp_content = doc_result
    
    context_msg = AIMessage(
        content=f"[Worker Result]: Document parsed.\n\n{resp_content}"
    )
    return {"messages": [context_msg], "next_step": "supervisor"}

async def image_worker_node(state: AthenaAgentState) -> Dict[str, Any]:
    from app.tools.registry import execute_tool
    from langchain_core.messages import AIMessage
    
    user_query = ""
    for msg in reversed(state.get("messages", [])):
        if getattr(msg, "type", "") == "human":
            user_query = str(msg.content)
            break

    print("[IMAGE WORKER] Executing image generation for:", user_query)
    gen_result = execute_tool("generate_image", user_query)
    
    context_msg = AIMessage(
        content=f"[Worker Result]: Image Generation Result:\n\n{gen_result}"
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

def synthesize_offline_response(user_query: str, worker_facts: list, facts_context: str, dept: str) -> str:
    query_str = (user_query or "").strip()
    query_lower = query_str.lower()
    full_text = "\n\n".join(worker_facts) if worker_facts else facts_context

    import re, datetime

    # 1. High-Precision Math Evaluation (e.g. 2+2=?, 15*8, calculate 100/4)
    expr_text = re.sub(r'^(?:what is|calculate|compute|eval|evaluate)\s+', '', query_str, flags=re.IGNORECASE)
    expr_text = re.sub(r'[\=\?]+$', '', expr_text).strip()
    if expr_text and re.match(r'^[0-9\.\s\+\-\*\/\%\(\)\^]+$', expr_text):
        expr_python = expr_text.replace('^', '**')
        try:
            res = eval(expr_python, {'__builtins__': None}, {})
            if isinstance(res, float) and res.is_integer():
                res = int(res)
            return f"**Calculation Result:**\n\n`{expr_text}` = **{res}**"
        except Exception:
            pass

    # 2. Time & Date Queries (e.g. what time is it?, what date is today?)
    time_keywords = ["what time", "current time", "what is time", "time now", "tell me the time", "current date", "what date", "today date", "today's date", "what is the date"]
    if any(kw in query_lower for kw in time_keywords):
        now = datetime.datetime.now()
        formatted_date = now.strftime("%A, %B %d, %Y")
        formatted_time = now.strftime("%I:%M:%S %p")
        return f"**Current Date & Time:**\n\n📅 **Date:** {formatted_date}\n⏰ **Time:** {formatted_time}"

    # 3. Image Visual Analysis Formatting — pass through actual worker results
    if "Image Visual Analysis" in full_text or "Vision Image Analysis" in full_text:
        fn_match = re.search(r"Analysis for '([^']+)'", full_text)
        filename_str = fn_match.group(1) if fn_match else "Uploaded Image"
        
        # Extract the actual vision model output (not a hardcoded template)
        vision_match = re.search(r"Vision Image Analysis for '[^']+':\n\n(.*)", full_text, re.DOTALL)
        if vision_match:
            vision_text = vision_match.group(1).strip()
            return f"### Image Analysis\n\n**File:** `{filename_str}`\n\n{vision_text}"
        
        ocr_match = re.search(r"\[Extracted Text \& Diagram Labels\]:\n(.*)", full_text, re.DOTALL)
        extracted_text = ocr_match.group(1).strip() if ocr_match else ""
        
        if extracted_text:
            return f"### Image & Visual Content Analysis\n\n**File:** `{filename_str}`\n\n**Extracted Text & Labels:**\n\n{extracted_text}"
        
        # Return whatever the worker actually produced, not a hardcoded template
        clean_vision = full_text.replace("[Worker Result]:", "").strip()
        if clean_vision:
            return f"### Image Analysis\n\n**File:** `{filename_str}`\n\n{clean_vision}"
        
        return f"### Image Analysis\n\n**File:** `{filename_str}`\n\nThe image was uploaded but the vision model could not process it. Please try uploading the image again."

    clean_lines = []
    if full_text:
        for line in full_text.splitlines():
            l_str = line.strip()
            if l_str and not l_str.startswith("[Worker Result]") and not l_str.startswith("[Retrieved Context"):
                clean_lines.append(l_str)
    
    clean_full_text = "\n".join(clean_lines)

    # 4. Author / Publisher queries
    if any(q in query_lower for q in ["author", "who wrote", "created by", "written by", "publisher", "issued by", "who is author"]):
        if clean_full_text:
            patterns = [
                r'(Government of India[^\.\n,]*)',
                r'(Ministry of [^\.\n,]*)',
                r'(Department of [^\.\n,]*)',
                r'(Author:\s*[^\.\n]+)',
                r'(Issued by:\s*[^\.\n]+)',
                r'(Prepared by:\s*[^\.\n]+)'
            ]
            matches = []
            for pat in patterns:
                found = re.findall(pat, clean_full_text, re.IGNORECASE)
                if found:
                    matches.extend(found)
            
            if matches:
                author_str = matches[0].strip()
                return f"**Author & Issuing Authority:**\nBased on the document context, the issuing authority / author is **{author_str}**."
            
            non_empty_lines = [l for l in clean_lines if len(l) > 5]
            if non_empty_lines:
                return f"**Author / Document Origin:**\nBased on the document context, this document is issued under: **{non_empty_lines[0]}**."

        return f"Please select or upload a document from your enterprise vault to query its author and origin."

    # 5. "what is this?" / Overview / Summary queries
    if any(q in query_lower for q in ["what is this", "summarize", "summary", "overview", "what document", "explain document", "about"]):
        if clean_full_text:
            header_lines = [l for l in clean_lines if len(l) > 10][:5]
            snippet = "\n".join(header_lines) if header_lines else clean_full_text[:400]
            return f"### Document Overview & Key Extracts\n\n{snippet}"

        return "This is your enterprise AI assistant. Upload or select a document from the left sidebar to analyze its contents."

    # 6. Targeted sentence matching for specific user queries
    if clean_full_text:
        query_words = [w for w in re.findall(r'\w+', query_lower) if len(w) > 3 and w not in ["what", "where", "when", "which", "how", "does", "is", "the", "that", "this", "them"]]
        matching_sentences = []
        for line in clean_lines:
            if any(qw in line.lower() for qw in query_words):
                matching_sentences.append(line)
        
        if matching_sentences:
            extracted_facts = "\n• " + "\n• ".join(matching_sentences[:5])
            return f"### Answer Grounded in Document Context\n{extracted_facts}"

        excerpt = "\n".join(clean_lines[:6])
        return f"### Relevant Document Context\n\n{excerpt}"

    # General fallback — answer common questions directly
    import datetime as _dt
    now = _dt.datetime.now()
    
    # Catch-all for time queries that weren't matched above
    if any(kw in query_lower for kw in ["time", "date", "clock", "day is it"]):
        formatted_date = now.strftime("%A, %B %d, %Y")
        formatted_time = now.strftime("%I:%M:%S %p")
        return f"📅 **Date:** {formatted_date}\n⏰ **Time:** {formatted_time}"
    
    # Catch-all for thanks / goodbye
    if any(kw in query_lower for kw in ["thank", "thanks", "appreciate"]):
        return "You're very welcome! Let me know if there's anything else I can help you with."
    if any(kw in query_lower for kw in ["bye", "goodbye", "see you"]):
        return "Goodbye! Have a wonderful day, and feel free to reach out whenever you need assistance."
    if any(kw in query_lower for kw in ["ok", "okay", "understand"]):
        return "Sounds good! Let me know how you'd like to proceed or if you have other questions."
    
    # For any other general question, give a helpful response
    return f"I'm Athena AI, your assistant. I can answer general questions, analyze documents, and help with many tasks. What would you like to know?"


async def final_synthesis_node(state: AthenaAgentState) -> Dict[str, Any]:
    """
    Consolidates agent thoughts, retrieved documents, database data,
    and memories into a final polished executive output.
    """
    dept = state.get("department_boundary", "GENERAL")
    
    import datetime
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")

    # Sprint 14: Fetch User Semantic Memories
    user_memories = []
    try:
        from app.memory.store import search_memories
        user_id = str(state.get("user_id", "default"))
        user_memories = search_memories(user_id=user_id, query="user preferences department identity facts", top_k=3)
    except Exception as e:
        print(f"[FINAL SYNTHESIS] Error retrieving user memories: {e}")

    # Format memories string if present
    memories_str = ""
    if user_memories:
        memories_str = "\n[User Preferences & Long-Term Semantic Memory]:\n" + "\n".join(user_memories)

    combined_m = state.get("context_metadata", {}).get("user_memories", [])
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
            if "No specific document matches found" not in clean_text:
                worker_facts.append(clean_text)

    facts_context = ("\n\n[Retrieved Context & Data]:\n" + "\n".join(worker_facts)) if worker_facts else ""

    # ⚡️ High-Performance Latency Accelerator:
    # Bypass re-synthesis ONLY for pre-formatted visual results (Vision AI, Image Generation).
    # For document parsing, PDFs, and invoices, proceed to synthesis so the AI formats line items, totals, and tables!
    if worker_facts and any(k in facts_context for k in ["Vision Image Analysis", "Image Generation Result"]):
        print("[SYNTHESIS ACCELERATOR] Direct return of pre-formatted visual result.")
        synthesized_text = "### Athena Document & Knowledge Synthesis\n\n" + "\n\n---\n\n".join(worker_facts)
        return {
            "messages": [AIMessage(content=synthesized_text)],
            "next_step": "END"
        }

    sys_msg = SystemMessage(
        content=(
            f"You are Athena AI, an intelligent and conversational AI assistant for the {dept} department. "
            f"Current system date and time: {current_time}. {memories_str}\n{facts_context}\n\n"
            "CORE BEHAVIOR — You are a GENERAL-PURPOSE AI assistant. You can:\n"
            "- Answer ANY general knowledge question accurately and thoroughly\n"
            "- Have natural conversations, explain concepts, write code, solve problems\n"
            "- Tell the current time/date when asked (use the system time provided above)\n"
            "- Analyze documents and data when provided by workers\n\n"
            "Instructions:\n"
            "1. If relevant enterprise documents or worker results are provided above, prioritize them to answer the user query.\n"
            "2. If no specific enterprise documents were found, answer the user query thoroughly and helpfully using your general AI knowledge. You are NOT limited to document queries — answer ANY question the user asks.\n"
            "3. For time/date questions: Use the 'Current system date and time' value provided above to give an accurate answer.\n"
            "4. Do NOT state that you lack information or refuse to answer simply because a document was not uploaded. Only mention missing documents if the user explicitly asked about a specific file.\n"
            "5. Do not cite internal system tags, worker labels, or metadata.\n"
            "6. DIAGRAMS: If the user asks for a diagram, flowchart, architecture, visual breakdown, or any structural visualization, you MUST provide:\n"
            "   a) A clean ASCII art box diagram using characters like +, -, |, > for boxes and arrows\n"
            "   b) AND/OR a Mermaid diagram code block (```mermaid ... ```)\n"
            "   Example ASCII style:\n"
            "   +----------------+     +----------------+\n"
            "   |   Frontend     | --> |   Backend API  |\n"
            "   +----------------+     +----------------+\n"
            "                                |\n"
            "                                v\n"
            "                         +----------------+\n"
            "                         |   Database     |\n"
            "                         +----------------+\n"
            "7. When answering from document context, cite targeted section facts or page numbers rather than dumping raw file text.\n"
            "8. Be conversational, helpful, and thorough. Give complete answers, not one-liners."
        )
    )
    
    compact_messages = [sys_msg, HumanMessage(content=user_query or "Hi")]

    # Sprint 27: Basic PII Scrubber Guardrail
    import re
    ssn_pattern = re.compile(r'\b\d{3}-\d{2}-\d{4}\b')
    for msg in compact_messages:
        if isinstance(msg.content, str):
            msg.content = ssn_pattern.sub("[REDACTED PII]", msg.content)

    # Generate the final response using real-time token streaming with a 25s timeout
    try:
        import asyncio
        async def _stream_llm():
            full_text = ""
            async for chunk in azure_llm.astream(compact_messages):
                c_text = getattr(chunk, "content", "")
                if isinstance(c_text, str):
                    full_text += c_text
            return AIMessage(content=full_text)
            
        response = await asyncio.wait_for(_stream_llm(), timeout=90.0)
        
        # Guard against false-positive safety refusals on benign enterprise queries
        refusal_keywords = [
            "illegal or harmful activities",
            "cannot create images",
            "cannot assist with this request",
            "i can't provide information",
            "copyright",
            "harmful activities"
        ]
        resp_text = getattr(response, "content", "")
        if any(kw in resp_text.lower() for kw in refusal_keywords) and worker_facts:
            print("[SAFETY OVERRIDE] Replacing false-positive refusal with worker facts synthesis.")
            # Filter out any refusal strings inside worker_facts
            clean_facts = [f for f in worker_facts if not any(kw in f.lower() for kw in refusal_keywords)]
            synth_content = "\n\n---\n\n".join(clean_facts) if clean_facts else "\n\n---\n\n".join(worker_facts)
            response = AIMessage(content="### Athena Knowledge & Document Synthesis\n\n" + synth_content)
    except Exception as e:
        print(f"[LLM FALLBACK WARNING] LLM invoke failed or timed out in final_synthesis: {e}")
        synthesized_text = synthesize_offline_response(user_query, worker_facts, facts_context, dept)
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
            wid = int(state.get("workspace_id", 1))
        except (ValueError, TypeError):
            wid = 1

        try:
            uid = int(state.get("user_id", 1))
        except (ValueError, TypeError):
            uid = 1
            
        token_record = TokenUsage(
            workspace_id=wid,
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