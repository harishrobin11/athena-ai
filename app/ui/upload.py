import streamlit as st
import requests


API_URL = "http://127.0.0.1:8000"


def render_upload():
    st.subheader("📄 Upload Documents")

    uploaded_file = st.file_uploader(
        "Choose a PDF",
        type=["pdf"],
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