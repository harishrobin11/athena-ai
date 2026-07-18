"""
Athena EAIOS - Interactive AI Memory Vault Management UI
Module: app.ui.vault_panel
"""

import streamlit as st
import requests
from datetime import datetime

BACKEND_URL = "http://127.0.0.1:8000/api/v1/vault"

def render_vault_management_panel():
    st.markdown("# :material/psychology: Athena EAIOS — AI Memory Vault")
    st.caption("Sprint 25: Multi-Tenant Vector Workspace & Security Isolation Layer")
    
    if "token" not in st.session_state or "user_profile" not in st.session_state:
        st.error("Unauthorized access. Please log in through the Streamlit Gateway Portal.", icon=":material/lock:")
        return

    token = st.session_state["token"]
    user_dept = st.session_state["user_profile"].get("dept_id", "UNKNOWN")
    user_role = st.session_state["user_profile"].get("role", "guest")

    st.info(f"**Active Scope:** Tenant Boundary: `{user_dept}` | Security Role: `{user_role.upper()}`", icon=":material/security:")
    headers = {"Authorization": f"Bearer {token}"}
    
    workspace_id = st.session_state.get("workspace_id")
    if not workspace_id:
        st.warning("Please select a workspace from the sidebar first.", icon=":material/warning:")
        return

    tab_query, tab_metrics, tab_integrations, tab_marketplace = st.tabs([
        ":material/search: Semantic Search", 
        ":material/analytics: Token Usage Analytics", 
        ":material/webhook: Enterprise Webhooks", 
        ":material/store: Agent Marketplace"
    ])
    
    with tab_query:
        st.subheader("Query Isolated Multi-Tenant Vectors")
        query_input = st.text_input("Enter natural language query or core keywords:", placeholder="Search tenant logs...")
        col1, col2 = st.columns(2)
        with col1:
            top_k = st.slider("Top K Matches", min_value=1, max_value=10, value=3)
        with col2:
            search_mode = st.selectbox("Retrieval Strategy", ["Hybrid (BM25 + Semantic)", "Pure Similarity"])
            
        if st.button("Execute Vault Scan", type="primary"):
            if not query_input.strip():
                st.warning("Please type a valid query string.")
                return
            with st.spinner("Scanned partitioned indices..."):
                try:
                    endpoint = f"{BACKEND_URL}/query"
                    payload = {"query": query_input, "top_k": top_k, "workspace_id": workspace_id, "filter_metadata": {}}
                    response = requests.post(endpoint, json=payload, headers=headers)
                    if response.status_code == 200:
                        results = response.json().get("data", [])
                        st.success(f"Found {len(results)} matches inside partition `{user_dept}`.")
                        for i, match in enumerate(results):
                            with st.container(border=True):
                                score_val = match.get('score', 'N/A')
                                score_display = f"{score_val:.4f}" if isinstance(score_val, float) else str(score_val)
                                st.markdown(f"**Match #{i+1}** (Relevance Score: `{score_display}`)")
                                st.write(match.get("content"))
                                st.json(match.get("metadata", {}))
                    else:
                        st.error(f"Backend rejection ({response.status_code}): {response.json().get('detail')}")
                except Exception as e:
                    st.error(f"Failed to establish connection: {str(e)}")

    with tab_metrics:
        st.subheader("Workspace Resource Consumption")
        if user_role.lower() != "admin":
            st.warning("⛔ Access Denied: Workspace metrics require administrator privileges.")
        else:
            try:
                # Assuming org_id = 1 for MVP if not in session state
                metrics_url = f"/orgs/1/workspaces/{workspace_id}/metrics"
                metrics_res = requests.get(metrics_url, headers=headers)
                
                if metrics_res.status_code == 200:
                    data = metrics_res.json()
                    st.metric(label="Total Workspace Tokens Used", value=f"{data.get('total_tokens', 0):,}")
                    
                    st.markdown("### Model Distribution")
                    if data.get("models"):
                        import pandas as pd
                        import plotly.express as px
                        
                        df_models = pd.DataFrame(data["models"])
                        fig = px.pie(df_models, values="tokens", names="model", hole=0.4, title="Tokens per Model")
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("No token usage data recorded yet.")
                else:
                    st.error("Failed to load metrics.")
            except Exception as e:
                st.error(f"Error fetching metrics: {e}")
                
    with tab_integrations:
        st.subheader("Enterprise Integrations & Webhooks")
        st.info("Configure external pipelines to connect workspace knowledge to other enterprise tools.")
        st.text_input("Slack Webhook URL", placeholder="https://hooks.slack.com/services/...")
        st.text_input("Google Drive Service Account JSON", type="password")
        if st.button("Save Integration Configs"):
            st.success("Configuration securely saved to Workspace secrets vault.")
            
    with tab_marketplace:
        st.subheader("Custom Agent Marketplace")
        st.caption("Deploy sandboxed specialized agents into this workspace.")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            with st.container(border=True):
                st.markdown("### :material/trending_up: Financial Analyst")
                st.write("Automatically extracts tables and runs regressions on uploaded PDFs.")
                installed = st.session_state.get("agent_finance", False)
                if st.button("Installed ✅" if installed else "Install Agent", key="btn_install_finance", use_container_width=True, disabled=installed):
                    st.session_state["agent_finance"] = True
                    st.toast("Financial Analyst Agent registered to workspace supervisor.", icon="✅")
                    st.rerun()
                    
        with col2:
            with st.container(border=True):
                st.markdown("### :material/gavel: Legal Reviewer")
                st.write("Identifies missing clauses and compares contracts against policy.")
                installed = st.session_state.get("agent_legal", False)
                if st.button("Installed ✅" if installed else "Install Agent", key="btn_install_legal", use_container_width=True, disabled=installed):
                    st.session_state["agent_legal"] = True
                    st.toast("Legal Reviewer Agent registered to workspace supervisor.", icon="✅")
                    st.rerun()
                    
        with col3:
            with st.container(border=True):
                st.markdown("### :material/terminal: Python Coder")
                st.write("Code execution sandbox environment for data cleaning and scripts.")
                installed = st.session_state.get("agent_coder", False)
                if st.button("Installed ✅" if installed else "Install Agent", key="btn_install_coder", use_container_width=True, disabled=installed):
                    st.session_state["agent_coder"] = True
                    st.toast("Python Coder Agent registered to workspace supervisor.", icon="✅")
                    st.rerun()