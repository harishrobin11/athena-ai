import json
import requests
import streamlit as st

API_URL = "http://127.0.0.1:8000"
CONVERSATION_API = f"{API_URL}/conversations"
TITLE_API = f"{CONVERSATION_API}"  # POST /conversations/{id}/title
CANCEL_API_URL = f"{API_URL}/cancel"
STREAM_API_URL = f"{API_URL}/chat/stream"
IMAGE_STREAM_API_URL = f"{API_URL}/chat/image/stream"

def get_auth_headers():
    return {
        "Authorization": f"Bearer {st.session_state['token']}"
    }


def sanitize_history(messages):
    sanitized = []
    for message in messages:
        sanitized.append(
            {
                "role": message.get("role"),
                "content": message.get("content", ""),
            }
        )
    return sanitized

CHAT_STYLE = """
<style>
body {
    background-color: #0b1120;
}
.block-container {
    padding: 1.5rem 1.5rem 2rem;
}
.chat-card {
    background: linear-gradient(180deg, #0f172a 0%, #111827 100%);
    border: 1px solid rgba(148, 163, 184, 0.12);
    border-radius: 28px;
    padding: 1.25rem;
    box-shadow: 0 30px 80px rgba(0, 0, 0, 0.28);
}
.chat-header {
    font-size: 1.5rem;
    font-weight: 700;
    color: #f8fafc;
    margin-bottom: 0.4rem;
}
.chat-subtitle {
    color: #94a3b8;
    margin-top: 0.1rem;
    margin-bottom: 1.5rem;
    line-height: 1.5;
}
.chat-panel {
    background: rgba(15, 23, 42, 0.72);
    border: 1px solid rgba(148, 163, 184, 0.14);
    border-radius: 30px;
    padding: 1rem;
}
.chat-input-wrap {
    display: flex;
    align-items: stretch;
    gap: 0.75rem;
}
.chat-upload-icon {
    width: 56px;
    height: 56px;
    border-radius: 18px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: rgba(39, 39, 59, 0.96);
    border: 1px solid rgba(148, 163, 184, 0.2);
    font-size: 1.35rem;
    cursor: pointer;
    color: #f8fafc;
}
.chat-upload-label {
    color: #94a3b8;
    text-align: center;
    font-size: 0.8rem;
    margin-top: 0.3rem;
}
.chat-input-box {
    width: 100%;
    background: #141b2e;
    border: 1px solid rgba(148, 163, 184, 0.16);
    border-radius: 30px;
    padding: 0.3rem 0.9rem;
}
.chat-input-box input {
    background: transparent !important;
    color: #e2e8f0 !important;
    border: none !important;
    padding: 1rem 0 !important;
    min-height: 3.6rem;
}
.chat-input-box input:focus {
    outline: none !important;
    box-shadow: none !important;
}
.chat-action-button {
    width: 100%;
    min-width: 54px;
    min-height: 54px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: #3b82f6;
    border-radius: 22px;
    border: 1px solid rgba(59, 130, 246, 0.65);
    color: #ffffff;
    font-size: 1.2rem;
    font-weight: 700;
}
.chat-action-button:hover {
    background: #2563eb;
}
.chat-stop-button {
    width: 100%;
    min-width: 54px;
    min-height: 54px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: #ef4444;
    border-radius: 22px;
    border: 1px solid rgba(239, 68, 68, 0.7);
    color: #ffffff;
    font-size: 1.2rem;
    font-weight: 700;
}
.chat-stop-button:hover {
    background: #dc2626;
}
.stTextInput > div > div > div {
    border-radius: 30px !important;
    border: 1px solid rgba(148, 163, 184, 0.16) !important;
}
.stTextInput > div > div > input {
    background: transparent !important;
    border: none !important;
    padding: 1rem 0.75rem !important;
    color: #e2e8f0 !important;
}
.stButton > button {
    border-radius: 22px !important;
    padding: 0.8rem 1rem !important;
    min-height: 54px;
}
.stFileUploader {
    border-radius: 20px;
    border: 1px solid rgba(148, 163, 184, 0.16);
    background: rgba(255, 255, 255, 0.03);
}
.upload-panel {
    background: rgba(15, 23, 42, 0.95);
    border: 1px solid rgba(148, 163, 184, 0.16);
    border-radius: 28px;
    padding: 1rem;
}
.upload-header {
    color: #f8fafc;
    font-size: 1rem;
    font-weight: 700;
    margin-bottom: 0.8rem;
}
.upload-footnote {
    color: #94a3b8;
    font-size: 0.88rem;
    margin-top: 0.6rem;
}
/* Ensure file input sits above other UI elements (fixes Safari picker not opening) */
.upload-panel {
    position: relative;
    z-index: 2;
}
.stFileUploader input[type="file"] {
    position: relative;
    z-index: 9999;
}

/* Force file input to be visible and clickable across browsers */
.stFileUploader input[type="file"] {
    display: block !important;
    opacity: 1 !important;
    width: 100% !important;
    height: 48px !important;
    pointer-events: auto !important;
    position: relative !important;
    z-index: 99999 !important;
}
</style>
"""


def render_chat():
    if "messages" not in st.session_state:
        st.session_state.messages = []

    if "generation_id" not in st.session_state:
        st.session_state.generation_id = None

    if "show_cancel" not in st.session_state:
        st.session_state.show_cancel = False

    if "upload_mode" not in st.session_state:
        st.session_state.upload_mode = False

    if "upload_widget_index" not in st.session_state:
        st.session_state.upload_widget_index = 0

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

    st.markdown(
        """
        <div class="chat-card">
            <div class="chat-header">Athena Chat</div>
            <div class="chat-subtitle">Ask Athena anything, attach an image or document, and get fast, polished answers.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            if "image" in message:
                st.image(
                    message["image"],
                    use_container_width=True,
                )
            st.markdown(message["content"])

    st.markdown("<div style='height: 1rem'></div>", unsafe_allow_html=True)

    def toggle_upload():
        # toggle upload panel; when opening, bump widget index so file_uploader
        # widgets are recreated with fresh keys (avoids stale widget state)
        new_mode = not st.session_state.get("upload_mode", False)
        st.session_state["upload_mode"] = new_mode
        if new_mode:
            st.session_state.upload_widget_index = (
                st.session_state.get("upload_widget_index", 0) + 1
            )

    def upload_document(file):
        files = {
            "file": (
                file.name,
                file.getvalue(),
                file.type or "application/pdf",
            )
        }
        response = requests.post(
            f"{API_URL}/upload",
            files=files,
            headers=get_auth_headers(),
            timeout=300,
        )
        response.raise_for_status()
        return response.json()["filename"]

    left_col, middle_col, right_col = st.columns([0.16, 0.7, 0.14])
    with left_col:
        # older style upload icon (paperclip) to toggle the upload panel
        st.button(
            "📎",
            key="upload_toggle",
            help="Toggle upload panel",
            on_click=toggle_upload,
            use_container_width=True,
        )

        st.markdown(
            "<div style='font-size:0.85rem;color:#94a3b8;text-align:center;margin-top:0.25rem;'>Attach files</div>",
            unsafe_allow_html=True,
        )

        # quick link to standalone upload test view
        if st.button("Upload Test Page", key="upload_test_page"):
            # import local upload renderer and show it
            try:
                from app.ui.upload import render_upload

                render_upload()
            except Exception as e:
                st.error(f"Failed to open upload test: {e}")

    with middle_col:
        prompt_text = st.text_input(
            "",
            key="chat_prompt",
            placeholder="Ask Athena anything...",
            label_visibility="collapsed",
        )

    selected_document = st.session_state.get(
        "selected_document",
        "All Documents",
    )

    image_widget_key = (
        f"chat_image_{st.session_state.upload_widget_index}"
    )
    document_widget_key = (
        f"chat_document_{st.session_state.upload_widget_index}"
    )

    send_visible = bool(
        (prompt_text and prompt_text.strip())
        or st.session_state.get(image_widget_key)
        or st.session_state.get(document_widget_key)
    )

    with right_col:
        send_pressed = False
        cancel_pressed = False
        if st.session_state.show_cancel:
            cancel_pressed = st.button(
                "✕",
                key="cancel_generation",
                help="Stop generation",
            )
        elif send_visible:
            send_pressed = st.button(
                "→",
                key="send_prompt",
                help="Send message",
            )

    uploaded_image = None
    uploaded_file = None

    if st.session_state.upload_mode:
        # render upload panel inline (avoid container wrapper which can
        # interfere with native file picker on some browsers/devices)
        st.markdown(
            """
            <div class='upload-panel'>
                <div class='upload-header'>Upload image or document</div>
                <div class='upload-footnote'>Select a JPG, PNG, or PDF file to attach with your next message.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        image_col, file_col = st.columns([1, 1])
        with image_col:
            st.markdown("**Upload Image**")
            uploaded_image = st.file_uploader(
                "Upload Image",
                type=["jpg", "jpeg", "png", "webp"],
                key=image_widget_key,
            )
        with file_col:
            st.markdown("**Upload Document**")
            uploaded_file = st.file_uploader(
                "Upload Document",
                type=["pdf"],
                key=document_widget_key,
            )

            if uploaded_image:
                st.image(
                    uploaded_image,
                    caption="Selected Image",
                    use_container_width=True,
                )

            if uploaded_file:
                st.markdown(f"**Uploaded document:** {uploaded_file.name}")
    else:
        uploaded_image = st.session_state.get(image_widget_key)
        uploaded_file = st.session_state.get(document_widget_key)

    prompt = None
    if cancel_pressed:
        generation_id = st.session_state.get("generation_id")
        if generation_id:
            requests.post(
                f"{CANCEL_API_URL}/{generation_id}",
                headers=get_auth_headers(),
                timeout=10,
            )
        st.session_state.show_cancel = False
        st.session_state.generation_id = None
        st.rerun()
    elif send_pressed and (
        (prompt_text and prompt_text.strip())
        or uploaded_image
        or uploaded_file
    ):
        if prompt_text and prompt_text.strip():
            prompt = prompt_text.strip()
        elif uploaded_image:
            prompt = "Please analyze the attached image."
        elif uploaded_file:
            prompt = "Please review the attached document."
        st.session_state.show_cancel = True
        st.session_state.upload_mode = False

    document_filename = None
    if prompt and uploaded_file:
        try:
            with st.spinner("Uploading attached document..."):
                document_filename = upload_document(uploaded_file)
            st.session_state["chat_document"] = None
        except Exception as exc:
            st.error(f"Document upload failed: {exc}")
            prompt = None

    if prompt:
        selected_documents = []
        if document_filename:
            selected_documents = [document_filename]
        elif selected_document != "All Documents":
            selected_documents = [selected_document]

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

        message = {
            "role": "user",
            "content": prompt,
        }

        if uploaded_image:
            message["image"] = uploaded_image

        if document_filename:
            message["document"] = document_filename

        st.session_state.messages.append(message)

        with st.chat_message("user"):
            if uploaded_image:
                st.image(
                    uploaded_image,
                    use_container_width=True,
                )
            st.markdown(prompt)

        answer = ""

        # rotate uploader keys to reset the widget state after send
        st.session_state.upload_widget_index += 1
        
        with st.chat_message("assistant"):
            placeholder = st.empty()
            placeholder.markdown("⏳ Athena is typing...")

        with st.chat_message("assistant"):

            placeholder = st.empty()

            try:
                placeholder.markdown("✍️ Athena is responding...")
                if uploaded_image:
                    uploaded_image_bytes = uploaded_image.getvalue()
                    response = requests.post(
                        IMAGE_STREAM_API_URL,
                        data={
                            "message": prompt,
                            "conversation_id":
                                st.session_state.get(
                                    "conversation_id"
                                ),
                            "selected_documents":
                                ""
                                if st.session_state.get(
                                    "selected_document",
                                    "All Documents",
                                )
                                == "All Documents"
                                else st.session_state.get(
                                    "selected_document"
                                ),
                        },
                        files={
                            "image": (
                                uploaded_image.name,
                                uploaded_image_bytes,
                                uploaded_image.type,
                            )
                        },
                        headers=get_auth_headers(),
                        stream=True,
                        timeout=300,
                    )

                else:

                    response = requests.post(
                        STREAM_API_URL,
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
                        stream=True,
                        timeout=120,
                    )

                response.raise_for_status()

                for line in response.iter_lines(
                    decode_unicode=True,
                ):

                    if not line:
                        continue

                    if not line.startswith("data: "):
                        continue

                    chunk = line[6:]

                    if chunk == "__END__":
                        break

                    if chunk.startswith("__GENERATION_ID__:"):

                        st.session_state.generation_id = (
                            chunk.replace(
                                "__GENERATION_ID__:",
                                ""
                            ).strip()
                        )

                        print(
                            "FRONTEND RECEIVED GENERATION ID =",
                            st.session_state.generation_id
                        )

                        continue

                    try:
                        chunk = json.loads(chunk)
                    except Exception:
                        pass

                    answer += chunk

                    placeholder.markdown(answer)

                placeholder.markdown(answer)
                st.session_state.generation_id = None

            except Exception as e:

                answer = f"❌ Error:\n\n{e}"

                placeholder.markdown(answer)

