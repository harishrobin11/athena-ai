from langgraph.graph import StateGraph, END
from app.services.agent_framework.state import AthenaAgentState
from app.services.agent_framework.supervisor import execute_supervisor
from app.services.agent_framework.nodes.rag import rag_worker_node

def create_athena_runtime_graph(llm):
    # Initialize state configuration matrix
    workflow = StateGraph(AthenaAgentState)
    
    # 1. Register backend core nodes
    workflow.add_node("supervisor", execute_supervisor)
    workflow.add_node("rag_worker", rag_worker_node)
    
    # 2. Wire up structural conditional routing paths
    workflow.set_entry_point("supervisor")
    
    # Direct routing edge mapping rules based on next_step field updates
    workflow.add_conditional_edges(
        "supervisor",
        lambda state: state["next_step"],
        {
            "rag_worker": "rag_worker",
            "FINISH": END
        }
    )
    
    # Worker nodes loop back into supervisor to evaluate final output synthesis
    workflow.add_edge("rag_worker", "supervisor")
    
    return workflow.compile()