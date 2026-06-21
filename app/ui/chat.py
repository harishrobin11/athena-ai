from urllib import response

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
                        "message": prompt,
                        "history": st.session_state.messages,
                    },
                    timeout=120,
                )

                response.raise_for_status()

                data = response.json()

                answer = data["response"]

                sources = data.get(
                    "sources",
                    [],
                )

                citation_text = ""

                if sources:

                    citation_text = "\n\n📚 Sources\n"

                    for source in sources:

                        citation_text += (
                            f"\n• {source['filename']} "
                            f"(Page {source['page']})"
                        )

                answer += citation_text

                sources = data.get(
                    "sources",
                    [],
                )
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