import os
import requests
import streamlit as st

def get_auth_headers():
    return {
        "Authorization":
        f"Bearer {st.session_state['token']}"
    }

API_URL = "http://127.0.0.1:8000/chat"
CONVERSATION_API = "http://127.0.0.1:8000/conversations"
TITLE_API = "http://127.0.0.1:8000/conversations"


def render_chat():
    
    st.header("💬 Athena")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    if (
        st.session_state.get("conversation_id")
        is not None
        and
        st.session_state.get(
            "loaded_conversation"
        )
        != st.session_state["conversation_id"]
    ):

        response = requests.get(
            f"{CONVERSATION_API}/"
            f"{st.session_state['conversation_id']}",
            headers=get_auth_headers(),
            timeout=10,
        )

        data = response.json()

        st.session_state.messages = [
            {
                "role": message["role"],
                "content": message["content"],
            }
            for message in data.get(
                "messages",
                [],
            )
        ]

        st.session_state[
            "loaded_conversation"
        ] = st.session_state[
            "conversation_id"
        ]
    # Display existing messages

    for message in st.session_state.messages:

        with st.chat_message(
            message["role"]
        ):
            st.markdown(
                message["content"]
            )       
        
    # User enters message
    if prompt := st.chat_input("Ask Athena anything..."):
        print("PROMPT =", prompt)
        print(
            "conversation_id =",
            st.session_state.get(
                "conversation_id"
            )
        )
        if st.session_state.get("conversation_id") is None:
            
            response = requests.post(
                CONVERSATION_API,
                headers=get_auth_headers(),
                timeout=10,
            )

            response.raise_for_status()

            data = response.json()

            st.session_state["conversation_id"] = data["id"]

            print(
                "Created conversation:",
                st.session_state["conversation_id"]
            )   
            
        if len(st.session_state.messages) == 0:
            title = prompt[:40]

            try:

                requests.put(
                    f"{TITLE_API}/"
                    f"{st.session_state['conversation_id']}"
                    f"/title",
                    json={
                        "title": title,
                    },
                    headers=get_auth_headers(),
                    timeout=10,
                )

            except Exception:
                pass

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
                        "conversation_id":
                            st.session_state.get(
                                "conversation_id"
                            ),
                        "selected_documents":
                            []
                            if st.session_state.get(
                                "selected_document",
                                "All Documents",
                            )
                            == "All Documents"
                            else [
                                st.session_state.get(
                                    "selected_document"
                                )
                            ],
                    },
                    headers=get_auth_headers(),
                    timeout=120,
                )
                print(response.status_code)
                print(response.text)

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