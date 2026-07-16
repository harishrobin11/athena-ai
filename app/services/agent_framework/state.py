from typing import TypedDict, Annotated, List, Dict, Any
from langchain_core.messages import BaseMessage
from operator import add

from typing import Annotated, TypedDict, List, Dict, Any
from langgraph.graph.message import add_messages

class AthenaAgentState(TypedDict):
    messages: Annotated[List[Any], add_messages]
    department_boundary: str
    execution_plan: List[str]
    next_step: str
    
    # Tenant and user isolation
    tenant_id: str
    workspace_id: str
    user_id: str
    
    # General dictionary to hold context, metadata, and tool output flags
    context_metadata: Dict[str, Any]
