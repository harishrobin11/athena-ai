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

        # Fetch Organizations for Multi-Tenant UI
        if "orgs_data" not in st.session_state:
            try:
                resp = requests.get("http://127.0.0.1:8000/orgs", headers=get_auth_headers(), timeout=5)
                if resp.status_code == 200:
                    st.session_state["orgs_data"] = resp.json()
                else:
                    st.session_state["orgs_data"] = []
            except:
                st.session_state["orgs_data"] = []
                
        orgs_data = st.session_state.get("orgs_data", [])

        with st.container(border=True):
            st.markdown("🏢 **Active Tenant**")
            
            if orgs_data:
                org_names = [org["name"] for org in orgs_data]
                selected_org_name = st.selectbox("Tenant", org_names, label_visibility="collapsed")
                selected_org = next(org for org in orgs_data if org["name"] == selected_org_name)
                
                st.session_state["tenant_id"] = str(selected_org["id"])
                st.session_state["role"] = selected_org["role"]
                st.session_state["department"] = selected_org["department"]
                
                role_color = "#4ADE80" if selected_org["role"].lower() == "admin" else "#FBBF24"
                st.markdown(f"<span style='font-size: 0.8rem; color: #94A3B8;'>Role: <span style='color: {role_color};'>{selected_org['role'].upper()}</span> | Dept: <span style='color: {role_color};'>{selected_org['department'].upper()}</span></span>", unsafe_allow_html=True)
                
                workspaces = selected_org.get("workspaces", [])
                if workspaces:
                    workspace_names = [w["name"] for w in workspaces]
                    selected_workspace_name = st.selectbox("Workspace", workspace_names, label_visibility="collapsed")
                    selected_workspace = next(w for w in workspaces if w["name"] == selected_workspace_name)
                    st.session_state["workspace_id"] = str(selected_workspace["id"])
                else:
                    st.warning("No Workspaces found.")
            else:
                st.warning("No Organizations found.")

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
            
        is_admin = any(org.get("role") in ["owner", "admin"] for org in orgs_data)
        if is_admin:
            if st.button("Organization Settings", use_container_width=True, type="secondary" if st.session_state.get("active_view") == "org_settings" else "primary"):
                st.session_state["active_view"] = "org_settings"
                st.rerun()

        # Check for SuperAdmin (Admin Portal)
        profile = st.session_state.get("user_profile", {})
        if profile.get("department") == "ADMIN" or profile.get("username") == "admin":
            if st.button("Admin Portal", use_container_width=True, type="secondary" if st.session_state.get("active_view") == "admin_portal" else "primary"):
                st.session_state["active_view"] = "admin_portal"
                st.rerun()
            if st.button("Prompt Studio", use_container_width=True, type="secondary" if st.session_state.get("active_view") == "prompt_studio" else "primary"):
                st.session_state["active_view"] = "prompt_studio"
                st.rerun()
            if st.button("Integration Hub", use_container_width=True, type="secondary" if st.session_state.get("active_view") == "integration_hub" else "primary"):
                st.session_state["active_view"] = "integration_hub"
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
        