import requests
import streamlit as st

API_URL = "http://127.0.0.1:8000/chat"


def render_chat():

    st.header("💬 Athena")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display previous messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # User enters message
    if prompt := st.chat_input("Ask Athena anything..."):

        st.session_state.messages.append(
            {
                "role": "user",
                "content": prompt,
            }
        )

        with st.chat_message("user"):
            st.markdown(prompt)

        with st.spinner("Athena is thinking..."):

            try:
                response = requests.post(
                    API_URL,
                    json={
                        "message": prompt
                    },
                    timeout=120,
                )

                response.raise_for_status()

                answer = response.json()["response"]

            except Exception as e:

                answer = f"❌ Error:\n\n{e}"

        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": answer,
            }
        )

        with st.chat_message("assistant"):
            st.markdown(answer)