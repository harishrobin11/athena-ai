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
    prompt_data = st.chat_input("Ask Athena anything...", accept_file="multiple")
    if prompt_data:
        # In newer Streamlit versions, prompt_data is an object with .text and .files attributes
        if hasattr(prompt_data, "text"):
            prompt = getattr(prompt_data, "text", "")
            files = getattr(prompt_data, "files", [])
        elif isinstance(prompt_data, dict):
            prompt = prompt_data.get("text", "")
            files = prompt_data.get("files", [])
        else:
            prompt = str(prompt_data)
            files = []
            
        print("PROMPT =", prompt)
        print("conversation_id =", st.session_state.get("conversation_id"))
        
        image_to_chat = None
        
        # Upload the files if present
        for uploaded_file in files:
            import mimetypes
            content_type, _ = mimetypes.guess_type(uploaded_file.name)
            if not content_type:
                content_type = "application/octet-stream"
            
            if content_type.startswith("image/"):
                image_to_chat = uploaded_file
                st.success(f"🖼️ Attached image: {uploaded_file.name}")
            else:
                payload_files = {
                    "file": (
                        uploaded_file.name,
                        uploaded_file.getvalue(),
                        content_type,
                    )
                }
                try:
                    upload_url = "http://127.0.0.1:8000/upload"
                    res = requests.post(
                        upload_url,
                        files=payload_files,
                        headers=get_auth_headers(),
                    )
                    if res.status_code == 200:
                        st.success(f"✅ Document {uploaded_file.name} uploaded successfully!")
                except Exception as e:
                    st.error(f"Failed to upload document {uploaded_file.name}: {e}")

        if not prompt and not files:
            st.stop()
            
        if not prompt and files:
            prompt = f"Uploaded {len(files)} files."

        if st.session_state.get("conversation_id") is None:
            response = requests.post(
                CONVERSATION_API,
                headers=get_auth_headers(),
                timeout=10,
            )
            response.raise_for_status()
            data = response.json()
            st.session_state["conversation_id"] = data["id"]
            
        if len(st.session_state.messages) == 0:
            title = prompt[:40]
            try:
                requests.put(
                    f"{TITLE_API}/{st.session_state['conversation_id']}/title",
                    json={"title": title},
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
                sel_docs = [] if st.session_state.get("selected_document", "All Documents") == "All Documents" else [st.session_state.get("selected_document")]
                
                if image_to_chat:
                    # Send to image endpoint
                    import mimetypes
                    content_type, _ = mimetypes.guess_type(image_to_chat.name)
                    if not content_type:
                        content_type = "image/jpeg"
                        
                    files_payload = {
                        "image": (image_to_chat.name, image_to_chat.getvalue(), content_type)
                    }
                    data_payload = {
                        "message": prompt,
                    }
                    if st.session_state.get("conversation_id"):
                        data_payload["conversation_id"] = st.session_state.get("conversation_id")
                    
                    if sel_docs:
                        # Ensure we format this correctly for form data list
                        data_payload["selected_documents"] = sel_docs
                        
                    response = requests.post(
                        "http://127.0.0.1:8000/chat/image",
                        data=data_payload,
                        files=files_payload,
                        headers=get_auth_headers(),
                        timeout=120,
                    )
                else:
                    # Send to text endpoint
                    response = requests.post(
                        API_URL,
                        json={
                            "message": prompt,
                            "history": st.session_state.messages,
                            "conversation_id": st.session_state.get("conversation_id"),
                            "selected_documents": sel_docs,
                        },
                        headers=get_auth_headers(),
                        timeout=120,
                    )

                response.raise_for_status()
                data = response.json()
                answer = data["response"]

                sources = data.get("sources", [])
                if sources:
                    citation_text = "\n\n📚 Sources\n"
                    for source in sources:
                        citation_text += f"\n• {source['filename']} (Page {source['page']})"
                    answer += citation_text

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