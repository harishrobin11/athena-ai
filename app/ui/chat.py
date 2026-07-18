import os
import requests
import streamlit as st

def get_auth_headers():
    return {
        "Authorization":
        f"Bearer {st.session_state['token']}"
    }

API_URL = "http://127.0.0.1:8000/api/v1/agent/chat"
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
                
                payload_data = {}
                if "workspace_id" in st.session_state:
                    payload_data["workspace_id"] = st.session_state["workspace_id"]
                    
                try:
                    upload_url = "http://127.0.0.1:8000/upload"
                    res = requests.post(
                        upload_url,
                        files=payload_files,
                        data=payload_data,
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
            status_box = st.empty()
            thought_box = st.empty()
            text_box = st.empty()
            
            accumulated_text = ""
            accumulated_thoughts = []
            
            try:
                # Prepare payload with multi-tenant context from session state
                req_payload = {
                    "message": prompt,
                    "department": st.session_state.get("department", "GENERAL"),
                    "tenant_id": st.session_state.get("tenant_id", "default"),
                    "workspace_id": st.session_state.get("workspace_id", "default")
                }
                
                with requests.post(API_URL, json=req_payload, stream=True, headers=get_auth_headers()) as response:
                    if response.status_code != 200:
                        st.error(f"Backend returned status code: {response.status_code}")
                    else:
                        import json
                        for line in response.iter_lines(decode_unicode=True):
                            if not line:
                                continue
                            
                            if line.startswith("data: "):
                                raw_json = line[6:].strip()
                                if not raw_json or raw_json == "__END__":
                                    continue
                                
                                try:
                                    event_data = json.loads(raw_json)
                                except Exception:
                                    if isinstance(raw_json, str):
                                        accumulated_text += json.loads(f'"{raw_json}"') if raw_json.startswith('"') else raw_json
                                        text_box.markdown(accumulated_text)
                                    continue
                                    
                                if isinstance(event_data, dict):
                                    if "error" in event_data:
                                        st.error(f"Backend Node Error: {event_data['error']}")
                                        continue
                                        
                                    event_type = str(event_data.get("event_type", "")).upper()
                                    node_name = event_data.get("node_name", "Orchestrator")
                                    content = event_data.get("content", "")
                                    
                                    if "THOUGHT" in event_type:
                                        accumulated_thoughts.append(f"**[{node_name}]**: {content}")
                                        with thought_box.expander("🛠️ View Agent Timeline", expanded=True):
                                            st.markdown("\\n\\n".join(accumulated_thoughts))
                                            
                                    elif "TOKEN" in event_type:
                                        accumulated_text += content
                                        text_box.markdown(accumulated_text)
                                        
                                    elif "FINAL" in event_type:
                                        status_box.empty()
                                        if not accumulated_text:
                                            text_box.markdown(content)
                                            accumulated_text = content
                                            
                                        sources = event_data.get("metadata", {}).get("sources", [])
                                        if sources:
                                            st.caption(f"📚 **Verified Source Contexts:** {', '.join(sources)}")
                                else:
                                    accumulated_text += str(event_data)
                                    text_box.markdown(accumulated_text)
                                    
                answer = accumulated_text

            except Exception as e:
                answer = f"❌ Error:\\n\\n{e}"

        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": answer,
            }
        )

        with st.chat_message("assistant"):
            st.markdown(answer)