import os
import pdfplumber
from typing import Dict, Any, List
from pydantic import BaseModel, Field

class LineItemSchema(BaseModel):
    description: str = Field(..., description="Description of item/service")
    quantity: float = Field(0.0, description="Quantity items")
    unit_price: float = Field(0.0, description="Unit cost")
    total_amount: float = Field(0.0, description="Total amount item")

class StructuredDocumentPayload(BaseModel):
    filename: str
    raw_text: str
    tables: List[List[List[str]]] = Field(default_factory=list, description="Extracted structural matrices")
    extracted_metadata: Dict[str, Any] = Field(default_factory=dict)

class DocumentIntelligenceProcessor:
    """Processes incoming complex financial documents with layout and table preservation."""
    
    def __init__(self):
        pass

    def process_pdf(self, file_path: str) -> StructuredDocumentPayload:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Target document path missing: {file_path}")

        extracted_text = []
        extracted_tables = []

        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text(layout=True)
                if text:
                    extracted_text.append(text)
                
                tables = page.extract_tables()
                for table in tables:
                    cleaned_table = [
                        [cell.strip() if cell else "" for cell in row]
                        for row in table if any(row)
                    ]
                    if cleaned_table:
                        extracted_tables.append(cleaned_table)

        full_text = "\n--- PAGE BREAK ---\n".join(extracted_text)
        heuristic_metadata = self._apply_heuristics(full_text)

        return StructuredDocumentPayload(
            filename=os.path.basename(file_path),
            raw_text=full_text,
            tables=extracted_tables,
            extracted_metadata=heuristic_metadata
        )

    def _apply_heuristics(self, text: str) -> Dict[str, Any]:
        metadata = {"invoice_number": "UNKNOWN", "grand_total": 0.0}
        for line in text.split("\n"):
            if "invoice" in line.lower() or "inv" in line.lower():
                metadata["invoice_number"] = line.strip()
            if "total" in line.lower() or "payable" in line.lower():
                metadata["grand_total"] = line.strip()
        return metadata