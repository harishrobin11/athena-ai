import os
from app.document_ai.processor import DocumentIntelligenceProcessor

# Initialize the structural engine processor
processor = DocumentIntelligenceProcessor()

from .registry import register_tool

@register_tool("analyze_document_layout")
def analyze_document_layout(tool_input: str, context: dict = None) -> str:
    """
    Parses a local PDF document's geometric layout and extracts structured table data.
    tool_input should be the target string filename (e.g., 'invoice.pdf').
    """
    filename = tool_input.strip()
    base_dir = os.path.join(os.getcwd(), "storage", "documents")
    file_path = os.path.join(base_dir, filename)
    
    # Check for multi-user subfolder structures (user_1, user_3, etc.)
    if not os.path.exists(file_path):
        found = False
        for root, dirs, files in os.walk(base_dir):
            if filename in files:
                file_path = os.path.join(root, filename)
                found = True
                break
        if not found:
            return f"Error: Document target '{filename}' could not be resolved in system storage."

    try:
        payload = processor.process_pdf(file_path)
        
        result_string = f"### Document Extraction & Content for {payload.filename}\n\n"
        if payload.raw_text and payload.raw_text.strip():
            result_string += f"#### [Extracted Document Text]\n{payload.raw_text.strip()}\n\n"

        result_string += "#### [Extracted Meta Indicators]\n"
        for k, v in payload.extracted_metadata.items():
            result_string += f"- **{k}**: {v}\n"
            
        result_string += "\n#### [Extracted Layout Tables]\n"
        if not payload.tables:
            result_string += "*No structured tables localized on page matrices.*\n"
        else:
            for idx, table in enumerate(payload.tables):
                result_string += f"\n**Table {idx + 1}:**\n"
                for row in table:
                    result_string += f"| {' | '.join(row)} |\n"
                    
        return result_string


    except Exception as e:
        return f"Execution Failure within Document AI Ingestion tool: {str(e)}"