"""
Athena AI - Core Framework
Module: app.tools.base
Description: Abstract Base Class establishing the global contract 
             for all downstream Agentic Tools and Execution Loops.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict
from pydantic import BaseModel

class BaseTool(ABC):
    """
    Abstract Base Class contract for AI Agentic workflow integrations.
    Provides structured schemas for agent router runtime profiling.
    """
    name: str
    description: str
    args_schema: type[BaseModel]

    def __init__(self) -> None:
        pass

    @abstractmethod
    def execute(self, *args: Any, **kwargs: Any) -> Dict[str, Any]:
        """Synchronous execution block mapping to the core tool function."""
        pass

    @abstractmethod
    async def execute_async(self, *args: Any, **kwargs: Any) -> Dict[str, Any]:
        """Asynchronous wrapper for performance optimization pipelines."""
        pass