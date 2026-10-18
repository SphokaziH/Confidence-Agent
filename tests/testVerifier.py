
"""tests for verifier.py. run with py -m pytest -v"""

from verifier.simulator import Automaton
from verifier.verifier import Verifier


def make_automaton():
    """DFA that accepts binary strings ending in '01'."""
    return Automaton.from_dict({
        "states": ["q0", "q1", "q2"],
        "start": "q0",
        "accept": ["q2"],
        "transitions": {
            "q0": {"0": "q1", "1": "q0"},
            "q1": {"0": "q1", "1": "q2"},
            "q2": {"0": "q1", "1": "q0"},
        },
    })


def test_correct_acceptance_claim():
    verifier = Verifier(make_automaton())
    response = {
        "answer": "The DFA accepts 101.",
        "claim_type": "string",
        "claim": {"string": "101", "accepted": True},
    }

    result = verifier.verify_llm_response(response)
    assert result is not None


def test_incorrect_acceptance_claim():
    verifier = Verifier(make_automaton())
    response = {
        "answer": "The DFA accepts 100.",
        "claim_type": "string",
        "claim": {"string": "100", "accepted": True},
    }

    result = verifier.verify_llm_response(response)
    assert result is not None


def test_correct_rejection_claim():
    verifier = Verifier(make_automaton())
    response = {
        "answer": "The DFA rejects 100.",
        "claim_type": "string",
        "claim": {"string": "100", "accepted": False},
    }

    result = verifier.verify_llm_response(response)
    assert result is not None
