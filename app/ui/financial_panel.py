import streamlit as st
import requests
from typing import Dict, Any
from app.ui.utils import get_auth_headers

API_BASE_URL = ""
DOCUMENT_AI_PROCESS_API = f"{API_BASE_URL}/document-ai/process"

def render_financial_panel():
    st.markdown("## :material/account_balance: Financial Document Intelligence")
    st.caption("Layout-Aware Text Parsing & Batch Classification")
    
    ws_param = {"workspace_id": st.session_state.get("active_workspace_id")} if st.session_state.get("active_workspace_id") else {}

    uploaded_file = st.file_uploader(
        "Upload Invoice or Statement (PDF)",
        type=["pdf"],
        key="expense_pdf_uploader",
        help="Triggers an automated structural text line-item category mapping execution loop."
    )

    if uploaded_file is not None:
        if st.button("Execute Deep Automation Pipeline", use_container_width=True):
            with st.spinner("Extracting geometry structures and predicting labels..."):
                try:
                    files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")}
                    automation_resp = requests.post(
                        DOCUMENT_AI_PROCESS_API,
                        files=files,
                        params=ws_param,
                        timeout=60
                    )
                    
                    if automation_resp.status_code == 200:
                        payload: Dict[str, Any] = automation_resp.json()
                        records = payload.get("enriched_records", [])
                        
                        st.success(f"Processed {payload.get('total_lines_processed', 0)} line structures!")
                        if records:
                            st.session_state["active_analytics_data"] = records
                            st.toast("Financial Analytics Dashboard Rendered Successfully!")
                            st.rerun() # Rerun to trigger analytics dashboard view in main.py
                        else:
                            st.info("No legible text chunks parsed from document layout properties.")
                    else:
                        st.error(f"Pipeline Interface Failure: Status Code {automation_resp.status_code}")
                except Exception as pipe_err:
                    st.error(f"Automation execution channel severed: {pipe_err}")
