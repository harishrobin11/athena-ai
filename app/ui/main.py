import streamlit as st

from app.ui.login import render_login
from app.ui.sidebar import render_sidebar
from app.ui.chat import render_chat
from app.ui.upload import render_upload

st.set_page_config(
    page_title="Athena AI",
    page_icon="🦉",
    layout="wide",
)

if not st.session_state.get(
    "authenticated",
    False
):
    render_login()
    st.stop()

render_sidebar()

st.title("🦉 Athena AI")
st.subheader(
    "Enterprise Knowledge Assistant"
)

left, right = st.columns([1, 2])

with left:
    render_upload()

with right:
    render_chat()