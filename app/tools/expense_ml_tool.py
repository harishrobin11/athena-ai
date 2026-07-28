from typing import List, Dict, Any
from ml.expense_classifier.model import ExpenseClassifierModel

class ExpenseClassificationTool:
    def __init__(self):
        self.name = "classify_corporate_expenses"
        self.description = (
            "Analyzes unstructured transaction line-items or raw narrative ledger records "
            "and maps them to accounting categories with predictive confidence scoring."
        )
        try:
            self.model = ExpenseClassifierModel()
        except Exception:
            self.model = None

    def execute(self, transaction_descriptions: List[str]) -> List[Dict[str, Any]]:
        if not self.model:
            return [{"category": "Unassigned Operations", "confidence": 0.0} for _ in transaction_descriptions]
        return self.model.predict(transaction_descriptions)