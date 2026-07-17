import streamlit as st
import requests

def get_auth_headers():
    return {
        "Authorization":
        f"Bearer {st.session_state['token']}"
    }
    
DOCUMENTS_API = "http://127.0.0.1:8000/documents"
CONVERSATIONS_API = "http://127.0.0.1:8000/conversations"
NEW_CHAT_API = "http://127.0.0.1:8000/conversations"
STATS_API = "http://127.0.0.1:8000/stats"

def render_sidebar():

    with st.sidebar:
        if st.button(
            "🚪 Logout",
            use_container_width=True,
        ):
            st.session_state.clear()
            st.rerun()
            
        st.title("🦉 Athena AI")

        st.divider()

        st.subheader("💬 Conversations")
        search_query = st.text_input(
            "🔍 Search",
            placeholder="Search conversations...",
            key="conversation_search",
        )        
        if st.button(
            "➕ New Chat",
            use_container_width=True,
        ):

            st.session_state["conversation_id"] = None
            st.session_state["messages"] = []
            st.session_state["loaded_conversation"] = None
            st.session_state["conversation_search"] = ""
            st.session_state["chat_prompt"] = ""
            st.session_state["chat_image"] = None
            st.session_state["chat_document"] = None

            st.rerun()

        try:

            if search_query:
                
                response = requests.get(
                    f"{CONVERSATIONS_API}/search",
                    params={"query": search_query},
                    headers=get_auth_headers(),
                    timeout=10,
                )

            else:

                response = requests.get(
                    CONVERSATIONS_API,
                    headers=get_auth_headers(),
                    timeout=10,
                )

            data = response.json()

            for conversation in data.get(
                "conversations",
                [],
            ):

                col1, col2 = st.columns([5, 1])

                with col1:

                    if st.button(
                        conversation["title"],
                        key=f"conv_{conversation['id']}",
                        use_container_width=True,
                    ):

                        st.session_state[
                            "conversation_id"
                        ] = conversation["id"]

                        st.rerun()

                with col2:

                    if st.button(
                        "🗑",
                        key=f"delete_{conversation['id']}",
                        use_container_width=True,
                    ):

                        requests.delete(
                            f"{CONVERSATIONS_API}/{conversation['id']}",
                            headers=get_auth_headers(),
                        )

                        if (
                            st.session_state.get(
                                "conversation_id"
                            )
                            == conversation["id"]
                        ):

                            st.session_state[
                                "conversation_id"
                            ] = None

                            st.session_state[
                                "messages"
                            ] = []

                        st.rerun()

        except Exception as e:

            st.error(
                f"Conversation Error: {e}"
            )

        st.divider()

        st.subheader("📚 Documents")
        try:

            response = requests.get(
                DOCUMENTS_API,
                headers=get_auth_headers(),
                timeout=10,
            )

            documents = response.json().get(
                "documents",
                []
            )

            if not documents:

                st.caption(
                    "No documents uploaded"
                )

            for document in documents:

                col1, col2 = st.columns(
                    [5, 1]
                )

                with col1:

                    st.write(
                        f"📄 {document['filename']}"
                    )

                with col2:

                    if st.button(
                        "🗑",
                        key=f"doc_{document['filename']}"
                    ):

                        requests.delete(
                            f"{DOCUMENTS_API}/"
                            f"{document['filename']}",
                            headers=get_auth_headers(),
                        )

                        st.rerun()
            if documents:
                
                if "selected_document" not in st.session_state:
                    st.session_state["selected_document"] = "All Documents"

                document_names = ["All Documents"]

                document_names.extend(
                    [
                        doc["filename"]
                        for doc in documents
                    ]
                )

                selected_document = st.radio(
                    "🔎 Search Scope",
                    document_names,
                )

                st.session_state[
                    "selected_document"
                ] = selected_document
        except Exception as e:

            st.error(
                f"Document Error: {e}"
            )
                
        if "conversation_id" in st.session_state:
            
            st.info(
                f"Conversation: "
                f"{st.session_state['conversation_id']}"
            )
        st.divider()

        st.subheader("📊 Athena Stats")

        try:

            response = requests.get(
                STATS_API,
                headers=get_auth_headers(),
                timeout=10,
            )

            stats = response.json()

            st.metric(
                "Documents",
                stats["documents"],
            )

            st.metric(
                "Conversations",
                stats["conversations"],
            )

            st.metric(
                "Messages",
                stats["messages"],
            )

        except Exception as e:

            st.error(
                f"Stats Error: {e}"
            )
        st.subheader("System")

        st.success("🟢 FastAPI Connected")
        st.success("🟢 Ollama Running")
        st.success("🟢 RAG Enabled")
        