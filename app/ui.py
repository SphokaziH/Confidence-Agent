import streamlit as st


def render_ui():

    st.title(
        "🤖 Theory of Computation Confidence Agent"
    )

    st.write(
        "This application verifies AI responses "
        "for Finite Automata questions."
    )


    st.divider()


    question = st.text_area(
        "Enter your Theory of Computation question:"
    )


    uploaded_file = st.file_uploader(
        "Upload automaton JSON"
    )


    if st.button("Submit"):

        st.success("Question submitted!")

        st.write("Question:")
        st.write(question)


        st.subheader("LLM Response")
        st.info(
            "Waiting for LLM integration..."
        )


        st.subheader("Verification")
        st.warning(
            "Waiting for verifier integration..."
        )


        st.subheader("Confidence")
        st.metric(
            "Confidence",
            "0%"
        )