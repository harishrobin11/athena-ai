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
    from app.rag.retriever import Retriever
    from app.memory.conversation_vector_store import ConversationVectorStore
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
    
    selected_docs = state.get("context_metadata", {}).get("selected_documents", [])
    if selected_docs:
        # Wrap multiple conditions in $and to satisfy Chroma requirements
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
    
    # Sprint 14: Conversation Intelligence - Fetch & Rank Memory
    past_conversations = []
    try:
        conv_docs = conv_store.search_messages(query=user_query, user_id=str(state["user_id"]), k=10)
        # Rank by recency (timestamp string ISO parsing not strictly necessary if ISO formatted, direct string sort works, but let's be safe)
        conv_docs.sort(key=lambda d: d.metadata.get("timestamp", ""), reverse=True)
        past_conversations = conv_docs[:5] # Keep the top 5 most recent matching messages
    except Exception as e:
        print(f"[RAG WORKER] Error retrieving past conversations: {e}")
        
    doc_context = "\n\n".join([d.page_content for d in docs]) if docs else "No relevant documents found in vault."
    
    conv_context = "\n\n".join([
        f"[{d.metadata.get('timestamp', 'Unknown')}] {d.metadata.get('role', 'Unknown').capitalize()}: {d.page_content}" 
        for d in past_conversations
    ]) if past_conversations else "No relevant past conversations found."

    combined_context = f"[Enterprise Documents]:\n{doc_context}\n\n[Past Conversations]:\n{conv_context}"

    context_msg = AIMessage(
        content=f"[Worker Result]: RAG fetch complete. Retrieved context:\n\n{combined_context}"
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
    
    user_query = ""
    for msg in reversed(state.get("messages", [])):
        if msg.type == "human":
            user_query = msg.content
            break

    # Extract filename using LLM
    extract_prompt = SystemMessage(
        content="Extract the exact PDF filename the user wants to analyze from the query. Return ONLY the filename (e.g. invoice.pdf). If no filename is found, return 'unknown.pdf'."
    )
    extract_query = HumanMessage(content=user_query)
    filename_response = await azure_llm.ainvoke([extract_prompt, extract_query])
    filename = filename_response.content.strip()

    print("[DOCUMENT WORKER] Processing document:", filename)
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
        content=f"You are a SQL expert. Based on the user's request, write a SELECT query against the following SQLite schema: {db_schema}. Return ONLY the raw SQL string without any markdown backticks or explanations."
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
            # Fallback to direct SQLite search for name declaration facts if no semantic memories found
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