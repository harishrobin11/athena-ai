import streamlit as st
from app.services.integrations.api_hub import api_hub

def render_integrations_panel():
    with st.container(border=True):
        st.markdown("""
            <h3 style="margin-top: 0;">Enterprise API Hub</h3>
            <p style="color: #94A3B8;">Connect Athena to external platforms securely. API keys are encrypted at rest.</p>
        """, unsafe_allow_html=True)
        
    st.markdown("### Active Connections")
    status = api_hub.get_connection_status()
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Slack", status["slack"].capitalize())
    with col2:
        st.metric("Microsoft Teams", status["teams"].capitalize())
    with col3:
        st.metric("Jira", status["jira"].capitalize())
    with col4:
        st.metric("Salesforce", status["salesforce"].capitalize())

    st.markdown("---")
    st.markdown("### Configure Integration")
    
    svc = st.selectbox("Platform", ["slack", "teams", "jira", "salesforce"])
    api_key = st.text_input("API Key / Bearer Token", type="password")
    
    if st.button("Connect Service", type="primary"):
        if api_hub.connect_service(svc, api_key):
            st.success(f"Successfully connected to {svc.capitalize()}!")
            st.rerun()
        else:
            st.error("Please provide a valid API Key.")
