import os
from typing import Dict, Any, Optional
from azure.core.credentials import AzureKeyCredential
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import AnalyzeResult
from app.core.logger import logger

class OCREngine:
    def __init__(self):
        self.endpoint = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT")
        self.key = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_KEY")
        
        if self.endpoint and self.key:
            self.client = DocumentIntelligenceClient(
                endpoint=self.endpoint, 
                credential=AzureKeyCredential(self.key)
            )
        else:
            self.client = None
            logger.warning("Azure Document Intelligence credentials not found. OCR will be disabled.")

    def analyze_invoice(self, file_bytes: bytes) -> Optional[Dict[str, Any]]:
        """
        Analyzes an invoice or receipt image/PDF and extracts structured fields 
        and bounding box lines.
        """
        if not self.client:
            raise ValueError("OCR Engine is not configured.")

        try:
            logger.info("Starting Azure Document Intelligence analysis for invoice...")
            # Use the pre-built invoice model
            poller = self.client.begin_analyze_document(
                "prebuilt-invoice", 
                analyze_request=file_bytes, 
                content_type="application/octet-stream"
            )
            result: AnalyzeResult = poller.result()
            
            extracted_data = {
                "content": result.content,
                "fields": {},
                "tables": []
            }

            if result.documents:
                for doc in result.documents:
                    for name, field in doc.fields.items():
                        extracted_data["fields"][name] = field.value_string or field.content
            
            # Extract basic table representations
            if result.tables:
                for table in result.tables:
                    table_info = {"rows": table.row_count, "columns": table.column_count, "cells": []}
                    for cell in table.cells:
                        table_info["cells"].append({
                            "row": cell.row_index,
                            "column": cell.column_index,
                            "content": cell.content
                        })
                    extracted_data["tables"].append(table_info)

            logger.info("Successfully analyzed invoice document.")
            return extracted_data

        except Exception as e:
            logger.error(f"OCR analysis failed: {e}")
            raise

ocr_engine = OCREngine()
