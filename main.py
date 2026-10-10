import streamlit as st
from app.ui import render_ui


st.set_page_config(
    page_title="Theory of Computation Confidence Agent",
    page_icon="🤖",
    layout="wide"
)


render_ui()