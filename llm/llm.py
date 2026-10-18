import os
import json
from dotenv import load_dotenv
import google.generativeai as genai


# -----------------------------
# LOAD API KEY
# -----------------------------

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise ValueError(
        "GEMINI_API_KEY not found. Add it to your .env file."
    )


genai.configure(
    api_key=API_KEY
)


# -----------------------------
# GEMINI MODEL
# -----------------------------

model = genai.GenerativeModel(
    "gemini-3.8-flash"
)


# -----------------------------
# GENERATE RESPONSE
# -----------------------------

def generate_response(question, automaton):

    prompt = f"""
You are a Theory of Computation expert.

Your task is to answer finite automata questions.

You MUST return ONLY valid JSON.
Do not include markdown.
Do not include explanations outside the JSON.

The JSON format must be:

{{
    "answer": "final natural language answer",
    "claim_type": "structure/string/regex",
    "claim": {{}}
}}


Rules:

1. If the question asks about the automaton structure:

Example:

{{
    "answer": "This is a DFA with three states.",
    "claim_type": "structure",
    "claim":
    {{
        "type": "DFA",
        "states": ["q0","q1"],
        "start": "q0",
        "accepting": ["q1"]
    }}
}}


2. If the question asks whether a string is accepted:

Example:

{{
    "answer": "The string is accepted.",
    "claim_type": "string",
    "claim":
    {{
        "string": "010",
        "accepted": true
    }}
}}


3. If the question asks for a regular expression:

Example:

{{
    "answer": "The regular expression is...",
    "claim_type": "regex",
    "claim":
    {{
        "regex": "a*b"
    }}
}}


Question:

{question}


Automaton:

{json.dumps(automaton, indent=2)}

"""


    response = model.generate_content(
        prompt
    )


    # Remove accidental markdown fences
    text = response.text.strip()

    if text.startswith("```"):
        text = text.replace("```json", "")
        text = text.replace("```", "")
        text = text.strip()


    # Validate JSON before returning
    try:

        json.loads(text)

    except Exception:

        return json.dumps(
            {
                "answer": text,
                "claim_type": "unknown",
                "claim": {}
            }
        )


    return text