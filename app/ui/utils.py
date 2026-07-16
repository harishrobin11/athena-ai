import streamlit as st

def get_auth_headers():
    return {
        "Authorization":
        f"Bearer {st.session_state['token']}"
    }