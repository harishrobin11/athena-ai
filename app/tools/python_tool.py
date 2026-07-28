"""
Python REPL Tool
Module: app.tools.python_tool
"""
import sys
import io
import traceback
import contextlib
from typing import Dict, Any, Optional

from .registry import register_tool

@register_tool("execute_python")
def execute_python_code(tool_input: str, context: Optional[Dict[str, Any]] = None) -> str:
    """
    Executes a snippet of Python code and returns the standard output.
    
    Parameters:
    - tool_input: The raw Python code to execute.
    - context: Unused.
    """
    code = tool_input.strip()
    # Strip markdown code blocks if present
    if code.startswith("```python"):
        code = code[9:]
    elif code.startswith("```"):
        code = code[3:]
    if code.endswith("```"):
        code = code[:-3]
    
    code = code.strip()
    
    output_buffer = io.StringIO()
    
    try:
        # Create an isolated global context
        isolated_globals = {}
        with contextlib.redirect_stdout(output_buffer):
            exec(code, isolated_globals)
        output = output_buffer.getvalue()
        if not output:
            return "Execution successful, but no output was printed."
        return output
    except Exception as e:
        error_trace = traceback.format_exc()
        return f"Error executing Python code:\n{error_trace}"
