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
    root_storage = os.path.join(os.getcwd(), "storage")
    
    # 1. Exact match search across all storage subtrees (documents, uploads, temp_uploads, etc.)
    file_path = None
    for root, dirs, files in os.walk(root_storage):
        if filename in files:
            file_path = os.path.join(root, filename)
            break
            
    # 2. Case-insensitive & partial stem match search
    if not file_path:
        fn_lower = filename.lower()
        clean_stem = os.path.splitext(fn_lower)[0]
        for root, dirs, files in os.walk(root_storage):
            for f in files:
                f_lower = f.lower()
                if f_lower == fn_lower or (len(clean_stem) > 4 and clean_stem in f_lower):
                    file_path = os.path.join(root, f)
                    break
            if file_path:
                break

    # 3. Fallback to most recent matching extension file if target file is not found
    if not file_path or not os.path.exists(file_path):
        import glob
        all_files = glob.glob(os.path.join(root_storage, "**", "*.*"), recursive=True)
        valid_files = [f for f in all_files if not f.endswith(('.db', '.DS_Store', '.py', '.json', '.pyc'))]
        if valid_files:
            valid_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
            ext = os.path.splitext(filename)[1].lower()
            for vf in valid_files:
                if ext and vf.lower().endswith(ext):
                    file_path = vf
                    break

    if not file_path or not os.path.exists(file_path):
        return f"Document '{filename}' was not found in storage. Please upload the file using the attach button, or select an existing document from your vault."

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