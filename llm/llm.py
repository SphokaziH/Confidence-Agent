import google.generativeai as genai


# Add your Gemini API key here
genai.configure(
    api_key="AQ.Ab8RN6JYt0PaNlbc70Mub_zyku72XB7oeB7qZzteTE5Ao6UCng"
)


model = genai.GenerativeModel(
    "gemini-3.8-flash"
)


def generate_response(question, automaton):

    prompt = f"""
You are a Theory of Computation expert.

Answer the following finite automata question.

Question:
{question}

Automaton:
{automaton}

Explain your reasoning clearly.
"""

    response = model.generate_content(prompt)

    return response.text