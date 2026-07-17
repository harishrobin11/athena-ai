"""
Web Search Tool - Powered by DuckDuckGo
Module: app.tools.web_search
"""
from typing import Dict, Any, Optional
from langchain_community.tools import DuckDuckGoSearchRun

def web_search_tool(tool_input: str, context: Optional[Dict[str, Any]] = None) -> str:
    """
    Executes a live internet search using DuckDuckGo to retrieve current facts, news, or general knowledge.
    
    Parameters:
    - tool_input: The search query string.
    - context: Unused for search.
    """
    try:
        search = DuckDuckGoSearchRun()
        result = search.invoke(tool_input)
        if not result:
            return "No internet search results found for the query."
        return result
    except Exception as e:
        return f"Error executing internet search: {str(e)}"
