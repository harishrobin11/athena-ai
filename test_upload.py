import streamlit as st

st.title("Upload Test")

uploaded_file = st.file_uploader("Choose a file")

if uploaded_file:
    st.success(f"Selected: {uploaded_file.name}")