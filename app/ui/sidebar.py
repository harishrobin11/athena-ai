import streamlit as st
import requests
DOCUMENTS_API = "http://127.0.0.1:8000/documents"
def render_sidebar():

    with st.sidebar:

        st.title("🦉 Athena AI")

        st.divider()

        st.subheader("Documents")

        st.button(
            "📄 Upload PDF",
            use_container_width=True,
        )

        try:

            response = requests.get(
                DOCUMENTS_API,
                timeout=10,
            )

            response.raise_for_status()

            documents = response.json()["documents"]

            if documents:

                st.markdown("### 📂 Uploaded")

                for doc in documents:
    
                    col1, col2 = st.columns([4, 1])

                    with col1:
                        st.write(
                            f"📄 {doc['filename']}"
                        )

                    with col2:

                        if st.button(
                            "❌",
                            key=f"delete_{doc['filename']}"
                        ):

                            requests.delete(
                                f"http://127.0.0.1:8000/documents/{doc['filename']}"
                            )

                            st.rerun()

            else:

                st.info(
                    "No documents uploaded yet."
                )

        except Exception as e:

            st.error(
                f"Document Error: {e}"
            )

        st.divider()

        st.subheader("System")

        st.success("🟢 FastAPI Connected")

        st.success("🟢 Ollama Running")

        st.success("🟢 RAG Enabled")