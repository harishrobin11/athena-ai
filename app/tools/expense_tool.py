"""
Athena AI - Sprint 20
Module: app.tools.expense_tool
Description: Production-grade Agentic Tool wrapper for the ExpenseClassifierModel.
             Provides structured execution schemas for LLM Planner/Router discovery.
"""

import os
from typing import Any, Dict, Optional
import joblib
from pydantic import BaseModel, Field

# Assuming a base tool contract exists in the architecture
from app.tools.base import BaseTool 


class ExpenseClassificationInput(BaseModel):
    """Schema for document or transaction text extraction inputs."""
    text_line: str = Field(
        ..., 
        description="The raw text snippet, line item, or invoice description to classify."
    )


class ExpenseClassifierTool(BaseTool):
    """
    Agentic Tool wrapper enabling LLM agents to programmatically route 
    extracted text lines to the serialized scikit-learn Logistic Regression pipeline.
    """
    name: str = "expense_classifier_tool"
    description: str = (
        "Useful for predicting standardized accounting categories and confidence scores "
        "from raw invoice text line items, receipts, or bank statements."
    )
    args_schema: type[BaseModel] = ExpenseClassificationInput

    def __init__(self, model_path: Optional[str] = None) -> None:
        super().__init__()
        # Establish default absolute pathing from project root environment
        self.model_path = model_path or os.path.join(
            "data", "models", "expense_classifier", "model.joblib"
        )
        self._model: Any = None
        self._preload_model()

    def _preload_model(self) -> None:
        """Loads the serialized joblib pipeline into memory with safety checks."""
        if not os.path.exists(self.model_path):
            raise FileNotFoundError(
                f"[CRITICAL] Serialized model artifact missing at: {self.model_path}. "
                "Ensure Sprint 19 seed workflow was executed successfully."
            )
        try:
            self._model = joblib.load(self.model_path)
        except Exception as e:
            raise RuntimeError(f"Failed to deserialize model checkpoint: {str(e)}")

    def execute(self, text_line: str) -> Dict[str, Any]:
        """
        Executes inference over the scikit-learn pipeline interface.
        """
        if not self._model:
            self._preload_model()

        try:
            prediction = self._model.predict([text_line])[0]
            probabilities = self._model.predict_proba([text_line])[0]
            
            confidence_score = float(max(probabilities))
            
            return {
                "success": True,
                "input_text": text_line,
                "category": str(prediction),  # Maps safely into route keys
                "confidence": round(confidence_score, 4),
                "error": None
            }
        except Exception as e:
            return {
                "success": False,
                "input_text": text_line,
                "category": "Unassigned Operations",
                "confidence": 0.0,
                "error": str(e)
            }

    async def execute_async(self, text_line: str) -> Dict[str, Any]:
        """Async variant mapping to synchronous execution wrapper for CPU-bound model."""
        import asyncio
        return await asyncio.to_thread(self.execute, text_line=text_line)


# ==========================================
# SPRINT 20 BRIDGE ALIAS
# ==========================================
ExpenseClassificationTool = ExpenseClassifierTool