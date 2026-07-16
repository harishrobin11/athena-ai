from .calculator import calculator_tool
from .document_search import search_documents_tool
from .conversation_search import search_conversations_tool
from .search_memory import search_memory
from .image_tool import execute as analyze_image
from .document_ai_tool import analyze_document_layout


TOOLS = {
    "calculator": calculator_tool,
    "search_documents": search_documents_tool,
    "search_conversations": search_conversations_tool,
    "search_memory": search_memory,
    "analyze_image": analyze_image,
    "analyze_document_layout": analyze_document_layout,  # Registered for Agent Orchestration
}


def execute_tool(
    tool_name,
    tool_input,
    context=None,
):
    """
    Execute a registered tool.

    Parameters
    ----------
    tool_name : str
        Name of the tool.

    tool_input : str
        User input passed to the tool.

    context : dict
        Runtime context (user_id, selected_documents,
        image_path, etc.)
    """

    tool = TOOLS.get(tool_name)

    if tool is None:
        raise ValueError(f"Unknown tool: {tool_name}")

    context = context or {}

    return tool(
        tool_input=tool_input,
        context=context,
    )