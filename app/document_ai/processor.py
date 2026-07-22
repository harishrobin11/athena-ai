import os
import pypdf
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

        try:
            import fitz
            doc = fitz.open(file_path)
            for page in doc:
                text = page.get_text("text")
                if text and text.strip():
                    extracted_text.append(text.strip())
                # Extract tables using PyMuPDF if available
                if hasattr(page, "find_tables"):
                    try:
                        tabs = page.find_tables()
                        for tab in tabs:
                            if hasattr(tab, "extract"):
                                table_data = tab.extract()
                                if table_data:
                                    extracted_tables.append([[str(cell or "") for cell in row] for row in table_data])
                    except Exception:
                        pass
        except Exception as ex:
            print(f"[PROCESSOR LOG] fitz reader failed, using pypdf fallback: {ex}")
            try:
                import pypdf
                reader = pypdf.PdfReader(file_path)
                for page in reader.pages:
                    text = page.extract_text()
                    if text:
                        extracted_text.append(text)
            except Exception as e:
                print(f"[PROCESSOR LOG] PDF reader error: {e}")

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