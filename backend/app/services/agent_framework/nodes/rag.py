from typing import Dict, Any
from langchain_core.messages import AIMessage
from app.rag.vector_store import VectorStore
from app.services.agent_framework.state import AthenaAgentState

# Instantiated once at backend component boundary
store = VectorStore()

async def rag_worker_node(state: AthenaAgentState) -> Dict[str, Any]:
    """
    Backend execution node that safely queries isolated vector partitions
    based on tenant context tracking headers.
    """
    messages = state.get("messages", [])
    last_user_message = messages[-1].content if messages else ""
    
    # 🔐 Enforce multi-tenant data boundaries from graph state
    dept_id = state.get("context_metadata", {}).get("dept_id") or "FINANCE"
    
    try:
        # Run the keyword/hybrid search suite built in Sprint 21
        matches = store.keyword_search(
            query=last_user_message,
            limit=3,
            filter_metadata={"dept_id": dept_id}
        )
        
        if not matches:
            context_response = f"No partitioned documents matched the query inside vault workspace: {dept_id}."
        else:
            context_response = "Retrieved context elements:\n" + "\n".join(
                [f"- {m['document']} (Score: {m['keyword_score']})" for m in matches]
            )
            
        # Append worker insight to backend state history and route back to supervisor
        return {
            "messages": messages + [AIMessage(content=context_response)],
            "next_step": "supervisor",  # Pass control back to orchestrator for synthesis
            "execution_plan": state.get("execution_plan", []) + ["Vector search completed"]
        }
        
    except Exception as e:
        return {
            "messages": messages + [AIMessage(content=f"RAG execution failure: {str(e)}")],
            "next_step": "FINISH"  # Fail-safe termination state
        }