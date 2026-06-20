import streamlit as st


def load_css():

    st.markdown(
        """
        <style>

        .block-container{
            padding-top:2rem;
        }

        </style>
        """,
        unsafe_allow_html=True,
    )