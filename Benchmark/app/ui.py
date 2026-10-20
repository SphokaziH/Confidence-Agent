import streamlit as st
import json
import os

from llm.llm import generate_response
from verifier.simulator import Automaton
from verifier.verifier import Verifier


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
# DISPLAY DIAGRAM
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
# DISPLAY AUTOMATON
# -----------------------------

def display_automaton(data):

    automaton = data.get(
        "automaton",
        data
    )


    st.subheader(
        "Automaton Information"
    )


    col1, col2 = st.columns(2)


    with col1:

        st.write("**Type**")
        st.write(
            automaton.get(
                "type",
                "Not provided"
            )
        )


        st.write("**States**")
        st.write(
            automaton.get(
                "states",
                "Not provided"
            )
        )


        st.write("**Alphabet**")
        st.write(
            automaton.get(
                "alphabet",
                "Not provided"
            )
        )



    with col2:

        st.write("**Start State**")
        st.write(
            automaton.get(
                "start_state",
                automaton.get(
                    "start",
                    "Not provided"
                )
            )
        )


        st.write("**Accepting States**")
        st.write(
            automaton.get(
                "accept_states",
                automaton.get(
                    "accept",
                    "Not provided"
                )
            )
        )



    st.divider()


    st.write(
        "**Transitions**"
    )

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
        "AI answer generation and verification "
        "for Finite Automata questions."
    )


    st.divider()



    diagrams = load_diagrams()

    questions = load_questions()



    if not diagrams:

        st.error(
            "No benchmark automata found."
        )

        return



    # -----------------------------
    # SELECT BENCHMARK
    # -----------------------------

    st.subheader(
        "Select Benchmark"
    )


    benchmark_ids = list(
        diagrams.keys()
    )


    selected_id = st.selectbox(
        "Choose automaton",
        benchmark_ids
    )


    selected_automaton = diagrams[selected_id]


    st.success(
        f"Selected: {selected_id}"
    )



    # -----------------------------
    # DISPLAY AUTOMATON
    # -----------------------------

    st.subheader(
        "Diagram"
    )


    display_diagram(
        selected_id
    )


    display_automaton(
        selected_automaton
    )



    # -----------------------------
    # QUESTION
    # -----------------------------

    st.subheader(
        "Question"
    )


    if selected_id in questions:

        selected_question = questions[selected_id]

        question_text = selected_question[0]

        st.write(
            question_text
        )

    else:

        st.warning(
            "No question found."
        )

        return



    # -----------------------------
    # SUBMIT
    # -----------------------------

    if st.button(
        "Submit"
    ):


        st.divider()


        # -----------------------------
        # GEMINI RESPONSE
        # -----------------------------

        st.subheader(
            "AI Response"
        )


        response = generate_response(
            question_text,
            selected_automaton
        )


        try:

            ai_data = json.loads(
                response
            )

        except Exception:

            st.error(
                "Gemini did not return valid JSON."
            )

            st.write(
                response
            )

            return



        st.write(
            ai_data.get(
                "answer",
                ""
            )
        )



        # -----------------------------
        # CLAIM EXTRACTION
        # -----------------------------

        st.subheader(
            "Extracted Claim"
        )


        claim_type = ai_data.get(
            "claim_type"
        )


        claim = ai_data.get(
            "claim"
        )


        st.write(
            "Claim type:",
            claim_type
        )


        st.json(
            claim
        )



        # -----------------------------
        # VERIFICATION
        # -----------------------------

        st.subheader(
            "Verification"
        )


        automaton = Automaton.from_dict(
            selected_automaton
        )


        verifier = Verifier(
            automaton
        )


        result = None



        if claim_type == "structure":


            result = verifier.verify_structure(
                claim
            )



        elif claim_type == "regex":


            result = verifier.verify_regex_claim(
                claim["regex"]
            )



        elif claim_type == "string":


            result = verifier.verify_string(
                claim["string"],
                claim["accepted"]
            )



        else:

            st.warning(
                "Unsupported claim type."
            )



        if result:


            st.text(
                result.pretty()
            )


            st.metric(
                "Confidence",
                f"{result.confidence:.0%}"
            )