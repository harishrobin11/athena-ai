import streamlit as st

from app.ui.login import render_login
from app.ui.sidebar import render_sidebar
from app.ui.chat import render_chat
from app.ui.upload import render_upload
from app.ui.styles import load_css

st.set_page_config(
    page_title="Athena AI",
    page_icon="🦉",
    layout="wide",
)

is_authenticated = st.session_state.get("authenticated", False)
load_css(is_login=not is_authenticated)

if not is_authenticated:
    render_login()
    st.stop()

render_sidebar()

# Add spacing at the top
st.markdown("<br><br>", unsafe_allow_html=True)

st.markdown("""
    <div style="margin-left: 2rem;">
        <h1 style="font-size: 3.5rem; font-weight: 800; letter-spacing: -1px; margin-bottom: 0;">
            :material/psychology: Athena AI
        </h1>
        <h2 style="font-size: 1.8rem; font-weight: 600; margin-top: 0.5rem; margin-bottom: 2rem;">Enterprise Knowledge Assistant</h2>
    </div>
""", unsafe_allow_html=True)

# Main centered welcome card
_, col_main, _ = st.columns([0.1, 0.8, 0.1])
with col_main:
    active_view = st.session_state.get("active_view", "chat")
    
    if active_view == "chat":
        with st.container(border=True):
            st.markdown("""
                <h3 style="margin-top: 0;">Athena Chat</h3>
                <p style="color: #94A3B8;">Ask Athena anything, attach an image or document.</p>
            """, unsafe_allow_html=True)
            
        render_chat()
    elif active_view == "vault":
        from app.ui.vault_panel import render_vault_management_panel
        render_vault_management_panel()
    elif active_view == "finance":
        from app.ui.financial_panel import render_financial_panel
        render_financial_panel()
    elif active_view == "ml":
        from app.ui.ml_panel import render_ml_panel
        render_ml_panel()
    elif active_view == "org_settings":
        from app.ui.org_settings import render_org_settings_panel
        render_org_settings_panel()
    elif active_view == "admin_portal":
        from app.ui.admin_portal import render_admin_portal
        render_admin_portal()