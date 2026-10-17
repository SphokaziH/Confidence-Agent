import google.generativeai as genai


# Add your Gemini API key here
genai.configure(
    api_key=" Placeholder key"
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