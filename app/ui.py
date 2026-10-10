import streamlit as st
import json
import os


def load_questions():

    path = "benchmark/questions.json"

    if not os.path.exists(path):
        return []

    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)



def load_automaton(automaton_id):

    path = f"benchmark/json/{automaton_id}.json"

    if not os.path.exists(path):
        return None

    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)



def render_ui():

    # -----------------------------
    # Header
    # -----------------------------

    st.title("🤖 Theory of Computation Confidence Agent")

    st.write(
        """
        This application evaluates AI-generated answers for
        Finite Automata questions using automated verification.
        """
    )

    st.divider()


    # -----------------------------
    # Load benchmark questions
    # -----------------------------

    questions = load_questions()


    if not questions:

        st.warning(
            "No benchmark questions found."
        )

        return



    # -----------------------------
    # Question Selection
    # -----------------------------

    st.subheader("Select Benchmark Question")


    question_options = {
        q["id"]: q
        for q in questions
    }


    selected_id = st.selectbox(
        "Choose a question:",
        question_options.keys()
    )


    selected_question = question_options[selected_id]


    st.divider()



    # -----------------------------
    # Display Question
    # -----------------------------

    st.subheader("Question")


    st.write(
        selected_question["question"]
    )



    # -----------------------------
    # Load Automaton
    # -----------------------------

    automaton_id = selected_question["automaton"]


    automaton = load_automaton(
        automaton_id
    )


    st.subheader("Automaton Information")


    if automaton:

        col1, col2 = st.columns(2)


        with col1:

            st.write("States")

            st.write(
                automaton["states"]
            )


        with col2:

            st.write("Alphabet")

            st.write(
                automaton.get(
                    "alphabet",
                    "Not specified"
                )
            )


    else:

        st.error(
            "Automaton JSON not found."
        )



    st.divider()



    # -----------------------------
    # Verification Button
    # -----------------------------

    if st.button("🔍 Run Verification"):

        st.info(
            "Verification pipeline will run here."
        )



    # -----------------------------
    # Results
    # -----------------------------


    st.subheader("Results")


    col1, col2, col3 = st.columns(3)


    with col1:

        st.metric(
            "Confidence",
            "Pending"
        )


    with col2:

        st.metric(
            "Verdict",
            "Pending"
        )


    with col3:

        st.metric(
            "Hallucination",
            "Pending"
        )



    st.subheader("AI Response")


    st.info(
        "LLM response will appear here."
    )


    st.subheader("Verification Evidence")


    st.info(
        "Evidence from verifier will appear here."
    )