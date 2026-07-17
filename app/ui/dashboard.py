import streamlit as st
import requests
import json
import os
import tempfile
from pathlib import Path

# Connect directly to our backend database and services for the Dashboard views
try:
    from app.memory.database import get_stats, list_documents, add_document, delete_document_by_user
    from app.services.document_service import DocumentService
    from app.services.storage_service import storage_service
except ImportError:
    # Fallbacks in case streamlit is run outside the main project path
    pass

st.set_page_config(page_title="Athena AI Enterprise Dashboard", layout="wide")

# Persistent state initialization
if "messages" not in st.session_state:
    st.session_state.messages = []

# Sidebar Navigation
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/8/8a/Google_Gemini_logo.svg/512px-Google_Gemini_logo.svg.png", width=50)
    st.title("Athena AI")
    st.markdown("Enterprise Workspace")
    page = st.radio("Navigation", ["💬 Chat Workspace", "📊 System Analytics", "📁 Document Vault"], label_visibility="collapsed")
    
    st.divider()
    st.caption("Active Profile: System Administrator")
    st.caption("Access Level: Clearance Level 5")

if page == "💬 Chat Workspace":
    st.title("🧠 Athena Copilot")
    st.markdown("Interact with the conversational AI and corporate memory framework.")
    
    # Render chat history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            
    # Chat Input Box
    if user_prompt := st.chat_input("Ask the Memory Vault orchestrator..."):
        with st.chat_message("user"):
            st.markdown(user_prompt)
        
        st.session_state.messages.append({"role": "user", "content": user_prompt})

        with st.chat_message("assistant"):
            status_box = st.empty()
            thought_box = st.empty()
            text_box = st.empty()
            
            accumulated_text = ""
            accumulated_thoughts = []
            
            # Using absolute path for local backend since Streamlit is a separate process
            backend_url = "http://127.0.0.1:8000/api/v1/chat/stream"
            req_payload = {"message": user_prompt, "department": "FINANCE"}
            
            try:
                with requests.post(backend_url, json=req_payload, stream=True) as response:
                    if response.status_code != 200:
                        st.error(f"Backend returned status code: {response.status_code}")
                    else:
                        for line in response.iter_lines(decode_unicode=True):
                            if not line:
                                continue
                            
                            if line.startswith("data: "):
                                raw_json = line[6:].strip()
                                if not raw_json or raw_json == "__END__":
                                    continue
                                
                                try:
                                    event_data = json.loads(raw_json)
                                except Exception:
                                    # Fallback for raw text strings vs JSON objects
                                    if isinstance(raw_json, str):
                                        accumulated_text += json.loads(f'"{raw_json}"') if raw_json.startswith('"') else raw_json
                                        text_box.markdown(accumulated_text)
                                    continue
                                    
                                if isinstance(event_data, dict):
                                    if "error" in event_data:
                                        st.error(f"Backend Node Error: {event_data['error']}")
                                        continue
                                        
                                    event_type = str(event_data.get("event_type", "")).upper()
                                    node_name = event_data.get("node_name", "Orchestrator")
                                    content = event_data.get("content", "")
                                    
                                    if "THOUGHT" in event_type:
                                        accumulated_thoughts.append(f"**[{node_name}]**: {content}")
                                        with thought_box.expander("🛠️ View Agent Timeline", expanded=True):
                                            st.markdown("\n\n".join(accumulated_thoughts))
                                            
                                    elif "TOKEN" in event_type:
                                        accumulated_text += content
                                        text_box.markdown(accumulated_text)
                                        
                                    elif "FINAL" in event_type:
                                        status_box.empty()
                                        if not accumulated_text:
                                            text_box.markdown(content)
                                            accumulated_text = content
                                            
                                        sources = event_data.get("metadata", {}).get("sources", [])
                                        if sources:
                                            st.caption(f"📚 **Verified Source Contexts:** {', '.join(sources)}")
                                else:
                                    # Handle simple strings directly yielded by the generator
                                    accumulated_text += str(event_data)
                                    text_box.markdown(accumulated_text)
                                    
                st.session_state.messages.append({"role": "assistant", "content": accumulated_text})
                
            except Exception as err:
                st.error(f"UI Stream Exception: {str(err)}\n\nMake sure the backend is running on port 8000.")


elif page == "📊 System Analytics":
    st.title("📊 Enterprise Analytics")
    st.markdown("Global telemetry and usage statistics for the Athena AI deployment.")
    
    try:
        stats = get_stats()
        
        with st.container(border=True):
            st.subheader("Platform Metrics")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Corporate Documents", f"{stats.get('documents', 0)}", border=True)
            with col2:
                st.metric("Total Conversations", f"{stats.get('conversations', 0)}", "+12% this week", border=True)
            with col3:
                st.metric("Messages Processed", f"{stats.get('messages', 0)}", border=True)
                
    except Exception as e:
        st.error(f"Failed to load analytics: {str(e)}")

elif page == "📁 Document Vault":
    st.title("📁 Document Vault")
    st.markdown("Manage corporate knowledge documents for RAG (Retrieval-Augmented Generation).")
    
    col_upload, col_list = st.columns([1, 2])
    
    with col_upload:
        with st.container(border=True):
            st.subheader("Upload Document")
            uploaded_file = st.file_uploader("Select a PDF to vectorize", type=["pdf"])
            if uploaded_file is not None:
                if st.button("Process & Vectorize", type="primary"):
                    with st.spinner("Ingesting document..."):
                        try:
                            # 1. Read file
                            file_bytes = uploaded_file.read()
                            # Default to admin user id = 1 for dashboard operations
                            user_id = 1
                            object_key = f"user_{user_id}/{uploaded_file.name}"
                            
                            # 2. Upload to storage
                            storage_service.upload_file(
                                file_content=file_bytes,
                                bucket="athena-documents",
                                object_name=object_key,
                                content_type="application/pdf"
                            )
                            
                            # 3. Create temp file for DocumentService
                            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                                tmp.write(file_bytes)
                                tmp_path = tmp.name
                                
                            # 4. Ingest via DocumentService
                            document_service = DocumentService()
                            chunks = document_service.ingest(tmp_path, user_id=user_id)
                            os.unlink(tmp_path)
                            
                            # 5. Add to Postgres database
                            add_document(user_id, uploaded_file.name, object_key=object_key)
                            
                            st.success(f"Successfully processed {chunks} vector chunks!")
                        except Exception as e:
                            st.error(f"Upload failed: {str(e)}")

    with col_list:
        with st.container(border=True):
            st.subheader("Indexed Documents")
            try:
                user_id = 1
                rows = list_documents(user_id)
                if not rows:
                    st.info("No documents have been indexed yet.")
                else:
                    for row in rows:
                        doc_id, filename, obj_key, uploaded_at, status = row
                        
                        col_name, col_status, col_action = st.columns([3, 2, 1])
                        col_name.write(f"📄 **{filename}**")
                        col_status.caption(f"{status.upper()} - {uploaded_at.strftime('%Y-%m-%d')}")
                        if col_action.button("Delete", key=f"del_{doc_id}", help="Remove from Vector Store"):
                            # Delete operation
                            delete_document_by_user(filename, user_id)
                            document_service = DocumentService()
                            document_service.delete_document(filename, user_id)
                            storage_service.delete_file("athena-documents", obj_key)
                            st.rerun()
                        st.divider()
            except Exception as e:
                st.error(f"Failed to fetch document list: {str(e)}")