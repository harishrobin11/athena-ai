"""
API Tool
Module: app.tools.api_tool
"""
import json
from typing import Dict, Any, Optional

from .registry import register_tool

@register_tool("execute_api")
def execute_api_call(tool_input: str, context: Optional[Dict[str, Any]] = None) -> str:
    """
    Mocks executing a REST API call.
    
    Parameters:
    - tool_input: A JSON string containing 'url', 'method', and optional 'payload'.
    - context: Unused.
    """
    try:
        data = json.loads(tool_input)
        url = data.get("url", "unknown_url")
        method = data.get("method", "GET").upper()
        payload = data.get("payload", {})
        
        # Mocking the HTTP request
        print(f"[API TOOL] Simulating {method} request to {url} with payload: {payload}")
        
        return json.dumps({
            "status": 200,
            "message": f"Successfully simulated {method} to {url}",
            "data": {"id": "mock_123", "processed": True}
        })
    except Exception as e:
        return f"Error executing API call: {str(e)}"
