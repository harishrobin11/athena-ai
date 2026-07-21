TOOLS = {}

def register_tool(name: str):
    """Decorator to dynamically register tools into the global registry."""
    def decorator(func):
        TOOLS[name] = func
        return func
    return decorator

# Import tools to trigger decorator registration
from .calculator import calculator_tool
from .document_search import search_documents_tool
from .conversation_search import search_conversations_tool
from .search_memory import search_memory
from .image_tool import execute as analyze_image
from .document_ai_tool import analyze_document_layout
from .web_search import web_search_tool
from .sql_tool import execute_sql_query
from .python_tool import execute_python_code
from .api_tool import execute_api_call
from .schedule_tool import schedule_task
from .api_hub_tools import slack_tool, jira_tool, salesforce_tool



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