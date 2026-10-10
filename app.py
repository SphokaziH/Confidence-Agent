import streamlit as st

st.title("Theory of Computation Confidence Agent")

st.write("Welcome!")

question = st.text_input("Ask a question")

if st.button("Submit"):
    st.write("This is where the answer will appear.")