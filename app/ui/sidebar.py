import streamlit as st


def render_sidebar():

    with st.sidebar:

        st.title("🦉 Athena AI")

        st.divider()

        st.subheader("Documents")

        st.button(
            "📄 Upload PDF",
            use_container_width=True,
        )

        st.divider()

        st.subheader("System")

        st.success("🟢 FastAPI Connected")

        st.success("🟢 Ollama Running")

        st.success("🟢 RAG Enabled")