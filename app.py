import streamlit as st

st.set_page_config(
    page_title="Theory of Computation Confidence Agent",
    page_icon="🤖",
    layout="wide"
)

st.title("🤖 Theory of Computation Confidence Agent")

st.write(
    "Welcome! This application helps verify AI responses for "
    "Finite Automata questions."
)

st.divider()

question = st.text_area(
    "Enter your Theory of Computation question:"
)

if st.button("Submit"):
    st.success("Question submitted!")
    st.write("Question:")
    st.write(question)

    st.write("### LLM Response")
    st.info("Coming soon...")

    st.write("### Verification")
    st.warning("Coming soon...")

    st.write("### Confidence")
    st.metric("Confidence", "0%")