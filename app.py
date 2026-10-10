import streamlit as st
from importlib import import_module

render_ui = import_module("app.ui").render_ui


st.set_page_config(
    page_title="Theory of Computation Confidence Agent",
    page_icon="🤖",
    layout="wide"
)


render_ui()