import os
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
        st.markdown("### :material/psychology: Athena EAIOS")
        st.markdown("<br>", unsafe_allow_html=True)

        with st.container(border=True):
            st.markdown("🏢 **Active Tenant**")
            st.selectbox("Tenant", ["Admin's Org", "Guest Org"], label_visibility="collapsed")
            st.markdown("<span style='font-size: 0.8rem; color: #94A3B8;'>Role: <span style='color: #4ADE80;'>ADMIN</span> | Dept: <span style='color: #4ADE80;'>ADMIN</span></span>", unsafe_allow_html=True)
            st.selectbox("Workspace", ["Default Workspace", "Finance Workspace"], label_visibility="collapsed")

        st.markdown("<br>", unsafe_allow_html=True)
        
        col_chat, col_vault = st.columns(2)
        with col_chat:
            if st.button("Operational Chat", use_container_width=True, type="secondary" if st.session_state.get("active_view") == "chat" else "primary"):
                st.session_state["active_view"] = "chat"
                st.rerun()
        with col_vault:
            if st.button("Memory Vault", use_container_width=True, type="secondary" if st.session_state.get("active_view") == "vault" else "primary"):
                st.session_state["active_view"] = "vault"
                st.rerun()

        if st.button("Financial Automation", use_container_width=True, type="secondary" if st.session_state.get("active_view") == "finance" else "primary"):
            st.session_state["active_view"] = "finance"
            st.rerun()

        if st.button("ML Classifier", use_container_width=True, type="secondary" if st.session_state.get("active_view") == "ml" else "primary"):
            st.session_state["active_view"] = "ml"
            st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)

        if st.button("↪ Logout", use_container_width=True, type="primary"):
            st.session_state.clear()
            st.rerun()
            
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("##### Recents\n**Search History**")

        search_query = st.text_input("Search", placeholder="Search conversations...", label_visibility="collapsed")        
        if st.button("+ New Chat", use_container_width=True, type="primary"):
            st.session_state["conversation_id"] = None
            st.session_state["messages"] = []
            st.session_state["loaded_conversation"] = None
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

            for conversation in data.get("conversations", []):
                is_selected = st.session_state.get("conversation_id") == conversation["id"]
                
                col1, col2 = st.columns([0.85, 0.15])
                with col1:
                    if st.button(
                        conversation["title"],
                        key=f"conv_{conversation['id']}",
                        use_container_width=True,
                        type="secondary" if is_selected else "tertiary"
                    ):
                        st.session_state["conversation_id"] = conversation["id"]
                        st.session_state["active_view"] = "chat"
                        st.rerun()
                with col2:
                    if is_selected:
                        if st.button(
                            ":material/delete:",
                            key=f"delete_{conversation['id']}",
                            use_container_width=True,
                            type="tertiary"
                        ):
                            requests.delete(
                                f"{CONVERSATIONS_API}/{conversation['id']}",
                                headers=get_auth_headers(),
                            )
                            if st.session_state.get("conversation_id") == conversation["id"]:
                                st.session_state["conversation_id"] = None
                                st.session_state["messages"] = []
                            st.rerun()
        except Exception as e:
            st.error(f"Conversation Error: {e}")
        