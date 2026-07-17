from langgraph.graph import StateGraph, END
from app.services.agent_framework.state import AthenaAgentState
from typing import Any
from app.services.agent_framework.supervisor import (
    supervisor_node,
    rag_worker_node,
    code_worker_node,
    research_worker_node,
    document_worker_node,
    sql_worker_node,
    final_synthesis_node
)

workflow = StateGraph(AthenaAgentState)

# 🔄 1. Register all specialized production worker blocks
workflow.add_node("supervisor", supervisor_node)
workflow.add_node("rag_worker", rag_worker_node)
workflow.add_node("code_worker", code_worker_node)
workflow.add_node("research_worker", research_worker_node)
workflow.add_node("document_worker", document_worker_node)
workflow.add_node("sql_worker", sql_worker_node)
workflow.add_node("final_synthesis", final_synthesis_node)

workflow.set_entry_point("supervisor")

# 🔀 2. Hook up active dynamic router conditionals
workflow.add_conditional_edges(
    "supervisor",
    lambda state: state["next_step"],
    {
        "rag_worker": "rag_worker",
        "code_worker": "code_worker",
        "research_worker": "research_worker",
        "document_worker": "document_worker",
        "sql_worker": "sql_worker",
        "FINISH": "final_synthesis"  # Send to synthesis to generate the text output block
    }
)

# Workers process documents/logic and automatically route back up to the master supervisor
workflow.add_edge("rag_worker", "supervisor")
workflow.add_edge("code_worker", "supervisor")
workflow.add_edge("research_worker", "supervisor")
workflow.add_edge("document_worker", "supervisor")
workflow.add_edge("sql_worker", "supervisor")

workflow.add_conditional_edges(
    "final_synthesis",
    lambda state: "END",
    {"END": END}
)

from langgraph.checkpoint.memory import MemorySaver

memory_checkpointer = MemorySaver()
compiled_graph = workflow.compile(checkpointer=memory_checkpointer)

def create_athena_runtime_graph(llm) -> Any:
    """Create and compile the Athena LangGraph runtime graph with a provided LLM.

    This helper is used by tests to inject a mock ``AzureChatOpenAI`` instance.
    """
    from app.services.agent_framework import supervisor as sup
    sup.azure_llm = llm

    # Re‑create the workflow with the patched nodes
    from langgraph.graph import StateGraph, END
    workflow = StateGraph(AthenaAgentState)
    workflow.add_node("supervisor", sup.supervisor_node)
    workflow.add_node("rag_worker", sup.rag_worker_node)
    workflow.add_node("code_worker", sup.code_worker_node)
    workflow.add_node("research_worker", sup.research_worker_node)
    workflow.add_node("document_worker", sup.document_worker_node)
    workflow.add_node("sql_worker", sup.sql_worker_node)
    workflow.add_node("final_synthesis", sup.final_synthesis_node)
    workflow.set_entry_point("supervisor")
    workflow.add_conditional_edges(
        "supervisor",
        lambda state: state["next_step"],
        {"rag_worker": "rag_worker", "code_worker": "code_worker", "research_worker": "research_worker", "document_worker": "document_worker", "sql_worker": "sql_worker", "FINISH": "final_synthesis"},
    )
    workflow.add_edge("rag_worker", "supervisor")
    workflow.add_edge("code_worker", "supervisor")
    workflow.add_edge("research_worker", "supervisor")
    workflow.add_edge("document_worker", "supervisor")
    workflow.add_edge("sql_worker", "supervisor")
    workflow.add_conditional_edges(
        "final_synthesis",
        lambda state: "END",
        {"END": END},
    )
    from langgraph.checkpoint.memory import MemorySaver
    test_memory = MemorySaver()
    return workflow.compile(checkpointer=test_memory)