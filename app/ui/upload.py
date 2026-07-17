import streamlit as st
import requests
import uuid

def get_auth_headers():
    return {
        "Authorization":
        f"Bearer {st.session_state['token']}"
    }

API_URL = "http://127.0.0.1:8000"


def render_upload():
    st.subheader("📄 Upload Documents")

    # give uploader a unique key to avoid duplicate auto-generated IDs
    uploaded_file = st.file_uploader(
        "Choose a PDF",
        type=["pdf"],
        key=f"standalone_upload_{uuid.uuid4().hex}",
    )

    if uploaded_file is not None:

        if st.button("Upload"):

            files = {
                "file": (
                    uploaded_file.name,
                    uploaded_file.getvalue(),
                    "application/pdf",
                )
            }

            with st.spinner("Uploading..."):

                response = requests.post(
                    f"{API_URL}/upload",
                    files=files,
                    headers=get_auth_headers(),
                )

            if response.status_code == 200:

                result = response.json()

                st.success(
                    f"✅ {result['filename']} uploaded successfully!"
                )

                st.write(
                    f"Chunks created: {result['chunks']}"
                )

            else:

                st.error("Upload failed.")
                st.write(response.text)