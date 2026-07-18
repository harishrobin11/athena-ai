import streamlit as st
import requests
import pandas as pd

def render_admin_portal():
    st.markdown("# :material/admin_panel_settings: Global Admin Portal")
    st.caption("Sprint 30: Platform Analytics & Operations")

    if "token" not in st.session_state or "user_profile" not in st.session_state:
        st.error("Unauthorized access.", icon=":material/lock:")
        return

    # Extra client-side guard (server also validates)
    profile = st.session_state["user_profile"]
    if profile.get("department") != "ADMIN" and profile.get("username") != "admin":
        st.error("SuperAdmin access required.", icon=":material/gavel:")
        return

    token = st.session_state["token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    tab_analytics, tab_users, tab_billing, tab_logs = st.tabs([
        ":material/bar_chart: Platform Analytics", 
        ":material/group: All Users", 
        ":material/payments: Tenant Billing", 
        ":material/list_alt: System Logs"
    ])
    
    with tab_analytics:
        res = requests.get("http://127.0.0.1:8000/admin/analytics", headers=headers)
        if res.status_code == 200:
            data = res.json().get("data", {})
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Total Users", data.get("total_users", 0))
            col2.metric("Total Organizations", data.get("total_orgs", 0))
            col3.metric("Total Workspaces", data.get("total_workspaces", 0))
            col4.metric("Total Documents", data.get("total_documents", 0))
            
            st.metric("Total Platform Tokens Consumed", data.get("total_tokens_consumed", 0))
        else:
            st.error("Failed to load analytics")
            
    with tab_users:
        res = requests.get("http://127.0.0.1:8000/admin/users", headers=headers)
        if res.status_code == 200:
            users = res.json().get("users", [])
            if users:
                df = pd.DataFrame(users)
                st.dataframe(df, use_container_width=True)
            else:
                st.info("No users found")
        else:
            st.error("Failed to load users")
            
    with tab_billing:
        res = requests.get("http://127.0.0.1:8000/admin/billing", headers=headers)
        if res.status_code == 200:
            orgs = res.json().get("data", [])
            if orgs:
                df = pd.DataFrame(orgs)
                st.dataframe(df, use_container_width=True)
            else:
                st.info("No organizations found")
        else:
            st.error("Failed to load billing data")
            
    with tab_logs:
        if st.button("Refresh Logs"):
            st.rerun()
            
        res = requests.get("http://127.0.0.1:8000/admin/logs", headers=headers)
        if res.status_code == 200:
            logs = res.json().get("logs", [])
            log_text = "\\n".join(logs)
            st.text_area("Live Server Logs", log_text, height=300)
        else:
            st.error("Failed to fetch logs")
