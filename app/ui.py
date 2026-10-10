import streamlit as st
import json
import os


# -----------------------------
# LOAD AUTOMATA JSON FILES
# -----------------------------

def load_diagrams():

    diagrams = {}

    folder = "benchmark/json"

    if not os.path.exists(folder):
        st.error("Benchmark JSON folder not found.")
        return diagrams


    for filename in os.listdir(folder):

        if filename.endswith(".json"):

            filepath = os.path.join(folder, filename)

            try:
                with open(filepath, "r", encoding="utf-8") as file:
                    diagrams[filename] = json.load(file)

            except json.JSONDecodeError:
                st.warning(
                    f"{filename} is not valid JSON and was skipped."
                )

    return diagrams



# -----------------------------
# LOAD QUESTIONS
# -----------------------------

def load_questions():

    filepath = "benchmark/questions.json"

    if not os.path.exists(filepath):
        return {}

    with open(filepath, "r", encoding="utf-8") as file:
        return json.load(file)



# -----------------------------
# DISPLAY AUTOMATON INFORMATION
# -----------------------------

def display_automaton(automaton):

    st.subheader("Automaton Information")

    col1, col2 = st.columns(2)


    with col1:

        st.write("**States**")
        st.write(
            automaton.get("states", "Not provided")
        )


        st.write("**Alphabet**")
        st.write(
            automaton.get("alphabet", "Not provided")
        )


    with col2:

        st.write("**Start State**")
        st.write(
            automaton.get(
                "start",
                automaton.get(
                    "start_state",
                    "Not provided"
                )
            )
        )


        st.write("**Accepting States**")
        st.write(
            automaton.get(
                "accept",
                automaton.get(
                    "accepting_states",
                    "Not provided"
                )
            )
        )


    st.divider()


    st.write("**Transitions**")

    st.json(
        automaton.get(
            "transitions",
            {}
        )
    )



# -----------------------------
# MAIN UI
# -----------------------------

def render_ui():

    st.set_page_config(
        page_title="Theory of Computation Confidence Agent",
        page_icon="🤖",
        layout="wide"
    )


    st.title(
        "🤖 Theory of Computation Confidence Agent"
    )


    st.write(
        "This application evaluates AI answers "
        "for Finite Automata questions."
    )


    st.divider()



    # Load data

    diagrams = load_diagrams()

    questions = load_questions()



    if not diagrams:

        st.error(
            "No automata JSON files found."
        )

        return



    # -----------------------------
    # SELECT DIAGRAM
    # -----------------------------

    selected_diagram = st.selectbox(
        "Select Automaton Diagram",
        diagrams.keys()
    )


    selected_automaton = diagrams[selected_diagram]


    st.success(
        f"Selected: {selected_diagram}"
    )


    display_automaton(
        selected_automaton
    )



    # -----------------------------
    # SELECT QUESTION
    # -----------------------------

    st.subheader(
        "Question"
    )


    if selected_diagram in questions:


        selected_question = st.selectbox(

            "Select Question",

            questions[selected_diagram]

        )


    else:

        selected_question = st.text_area(

            "Enter Question"

        )



    # -----------------------------
    # SUBMIT SECTION
    # -----------------------------


    if st.button("Submit"):


        st.divider()


        st.subheader(
            "AI Response"
        )

        st.info(
            "LLM integration coming soon..."
        )


        st.subheader(
            "Verification"
        )

        st.warning(
            "Verifier integration coming soon..."
        )


        st.subheader(
            "Confidence Score"
        )

        st.metric(
            "Confidence",
            "0%"
        )