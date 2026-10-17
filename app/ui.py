import streamlit as st
import json
import os


# -----------------------------
# LOAD AUTOMATA JSON FILES
# -----------------------------

def load_diagrams():

    diagrams = {}

    folder = "Benchmark/JSON files"

    if not os.path.exists(folder):
        st.error("Benchmark JSON folder not found.")
        return diagrams


    for filename in os.listdir(folder):

        if filename.endswith(".json"):

            filepath = os.path.join(folder, filename)

            with open(filepath, "r", encoding="utf-8") as file:
                diagrams[filename] = json.load(file)


    return diagrams


# -----------------------------
# LOAD QUESTIONS
# -----------------------------

def load_questions():

    filepath = "Benchmark/questions.json"

    if not os.path.exists(filepath):
        return {}

    with open(filepath, "r", encoding="utf-8") as file:
        return json.load(file)
    
# -----------------------------
# LOAD Images
# -----------------------------

def display_diagram(selected_id):

    image_name = selected_id.replace(".json", ".png")

    image_path = f"Benchmark/Diagrams/{image_name}"

    if os.path.exists(image_path):

        st.image(
            image_path,
            caption=selected_id
        )

    else:

        st.warning(
            f"Diagram image not found: {image_path}"
        )
# -----------------------------
# DISPLAY AUTOMATON INFORMATION
# -----------------------------

def display_automaton(data):

    # Extract the actual automaton information
    automaton = data.get("automaton", data)

    st.subheader("Automaton Information")

    col1, col2 = st.columns(2)


    with col1:

        st.write("**Type**")
        st.write(
            automaton.get("type", "Not provided")
        )

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
                "start_state",
                "Not provided"
            )
        )


        st.write("**Accepting States**")
        st.write(
            automaton.get(
                "accept_states",
                "Not provided"
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

    benchmark_ids = [
    filename
    for filename in diagrams.keys()
    ]

    selected_id = st.selectbox(
        "Select Benchmark",
            benchmark_ids
    )
    selected_automaton = diagrams[selected_id]

    st.success(
    f"Selected: {selected_id}"
    )


    st.subheader("Diagram")

    display_diagram(selected_id)


    display_automaton(
        selected_automaton
    )



    # -----------------------------
    # SELECT QUESTION
    # -----------------------------

    st.subheader("Question")


    if selected_id in questions:

        selected_question = questions[selected_id]

        st.write(selected_question[0])

    else:

        st.warning(
            "No question found for this benchmark"
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