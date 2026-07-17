import os
import streamlit as st
import requests
import base64

LOGIN_API = "http://127.0.0.1:8000/login"
REGISTER_API = "http://127.0.0.1:8000/register"

def get_base64_of_bin_file(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

def render_login():
    # Center the login form using columns
    _, col2, _ = st.columns([1, 1.2, 1])
    
    with col2:
        st.markdown("<br><br><br>", unsafe_allow_html=True) # Add some top spacing
        
        # Header with inline image and text
        brain_b64 = ""
        if os.path.exists("app/ui/assets/brain.png"):
            brain_b64 = get_base64_of_bin_file("app/ui/assets/brain.png")
            
        st.markdown(f"""
            <div style="text-align: center; margin-bottom: 2rem;">
                <img src="data:image/png;base64,{brain_b64}" width="60" style="vertical-align: middle; margin-right: 15px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.3);">
                <span style="font-size: 3.5rem; font-weight: 800; vertical-align: middle; letter-spacing: -1px;">Athena AI</span>
                <p style="color: #94A3B8; font-size: 1.2rem; margin-top: 1rem;">Enterprise AI Operating System<br>(EAIOS) Gateway Portal</p>
            </div>
        """, unsafe_allow_html=True)

        with st.container(border=True):
            login_tab, register_tab = st.tabs(["Login", "Register"])

            with login_tab:
                username = st.text_input("Username", key="login_username")
                password = st.text_input("Password", type="password", key="login_password")
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("Login", use_container_width=True):
                    try:
                        response = requests.post(
                            LOGIN_API,
                            json={"username": username, "password": password},
                            timeout=10,
                        )
                        response.raise_for_status()
                        data = response.json()
                        st.session_state["token"] = data["access_token"]
                        st.session_state["authenticated"] = True
                        st.rerun()
                    except Exception as e:
                        st.error(f"Login failed: {e}")

            with register_tab:
                username = st.text_input("Username", key="register_username")
                email = st.text_input("Email", key="register_email")
                password = st.text_input("Password", type="password", key="register_password")
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("Register", use_container_width=True):
                    try:
                        response = requests.post(
                            REGISTER_API,
                            json={"username": username, "email": email, "password": password},
                            timeout=10,
                        )
                        response.raise_for_status()
                        st.success("User created successfully. Please login.")
                    except Exception as e:
                        st.error(f"Registration failed: {e}")