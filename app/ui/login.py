import os
import streamlit as st
import requests

LOGIN_API = "http://127.0.0.1:8000/login"
REGISTER_API = "http://127.0.0.1:8000/register"


def render_login():

    st.title("🦉 Athena AI")

    login_tab, register_tab = st.tabs(
        ["Login", "Register"]
    )

    with login_tab:

        username = st.text_input(
            "Username",
            key="login_username",
        )

        password = st.text_input(
            "Password",
            type="password",
            key="login_password",
        )

        if st.button(
            "Login",
            use_container_width=True,
        ):

            try:

                response = requests.post(
                    LOGIN_API,
                    json={
                        "username": username,
                        "password": password,
                    },
                    timeout=10,
                )

                response.raise_for_status()

                data = response.json()

                st.session_state["token"] = (
                    data["access_token"]
                )

                st.session_state[
                    "authenticated"
                ] = True

                st.rerun()

            except Exception as e:

                st.error(
                    f"Login failed: {e}"
                )

    with register_tab:

        username = st.text_input(
            "Username",
            key="register_username",
        )

        email = st.text_input(
            "Email",
            key="register_email",
        )

        password = st.text_input(
            "Password",
            type="password",
            key="register_password",
        )

        if st.button(
            "Register",
            use_container_width=True,
        ):

            try:

                response = requests.post(
                    REGISTER_API,
                    json={
                        "username": username,
                        "email": email,
                        "password": password,
                    },
                    timeout=10,
                )

                response.raise_for_status()

                st.success(
                    "User created successfully. "
                    "Please login."
                )

            except Exception as e:

                st.error(
                    f"Registration failed: {e}"
                )