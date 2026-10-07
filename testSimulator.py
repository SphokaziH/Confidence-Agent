"""
test_simulator.py - checks simulator.py against answers we know are correct.

Run:  python test_simulator.py
(also works with:  pytest test_simulator.py)
"""

from simulator import Automaton

# DFA: binary strings ending in "01"
ENDS_01 = Automaton.from_dict({
    "states": ["q0", "q1", "q2"],
    "start": "q0",
    "accept": ["q2"],
    "transitions": {
        "q0": {"0": "q1", "1": "q0"},
        "q1": {"0": "q1", "1": "q2"},
        "q2": {"0": "q1", "1": "q0"},
    },
})

# NFA (guesses where the suffix starts): also "ends in 01"
NFA_ENDS_01 = Automaton.from_dict({
    "states": ["a", "b", "c"],
    "start": "a",
    "accept": ["c"],
    "transitions": {"a": {"0": ["a", "b"], "1": "a"}, "b": {"1": "c"}},
})

# NFA with an epsilon move: accepts "", "1", "11", ... (only 1s)
EPS_NFA = Automaton.from_dict({
    "states": ["s", "t"],
    "start": "s",
    "accept": ["t"],
    "transitions": {"s": {"eps": "t"}, "t": {"1": "t"}},
})

# DFA: strings ending in "1"
ENDS_1 = Automaton.from_dict({
    "states": ["p", "q"],
    "start": "p",
    "accept": ["q"],
    "transitions": {"p": {"0": "p", "1": "q"}, "q": {"0": "p", "1": "q"}},
})


def test_accepts_and_rejects():
    for s in ["01", "101", "1001", "0001"]:
        assert ENDS_01.accepts(s), f"{s} should be accepted"
    for s in ["", "0", "1", "10", "111", "100", "010"]:
        assert not ENDS_01.accepts(s), f"{s} should be rejected"


def test_trace_matches_accepts():
    for s in ["", "0", "01", "1001", "110"]:
        assert ENDS_01.trace(s).accepted == ENDS_01.accepts(s)
    t = ENDS_01.trace("01")
    assert [st.symbol for st in t.steps] == ["0", "1"]
    assert t.final_states == frozenset({"q2"})


def test_nfa_and_epsilon():
    assert NFA_ENDS_01.accepts("1001") and not NFA_ENDS_01.accepts("10")
    assert EPS_NFA.accepts("") and EPS_NFA.accepts("111")
    assert not EPS_NFA.accepts("0")


def test_structure():
    assert ENDS_01.summary()["type"] == "DFA"
    assert NFA_ENDS_01.summary()["type"] == "NFA"
    assert EPS_NFA.has_epsilon_transitions()
    assert ENDS_01.is_complete()
    assert ("b", "0") in NFA_ENDS_01.missing_transitions()
    assert ("q0", "1") in ENDS_01.self_loops()


def test_claim_checking():
    good = ENDS_01.check_claim(lambda s: s.endswith("01"))
    assert good.consistent and good.agreement_rate == 1.0
    bad = ENDS_01.check_claim(lambda s: s.endswith("10"))
    assert not bad.consistent and bad.counterexamples
    s, real, claimed = bad.counterexamples[0]
    assert real != claimed
    assert ENDS_01.check_claim_regex(r"[01]*01").consistent


def test_generate_test_strings():
    a = ENDS_01.generate_test_strings(n=12, max_len=5)
    b = ENDS_01.generate_test_strings(n=12, max_len=5)
    assert a == b                                   # reproducible
    assert len(a) == len(set(a)) and len(a) <= 12   # no duplicates
    assert "" in a
    results = {ENDS_01.accepts(s) for s in a}
    assert results == {True, False}                 # mix of both


def test_equivalence():
    assert NFA_ENDS_01.is_equivalent(ENDS_01)       # NFA == DFA
    assert ENDS_01.find_difference(ENDS_1) == "1"   # shortest difference
    assert ENDS_01.find_difference(ENDS_01) is None


def test_bad_input_is_rejected():
    for bad in [
        {"states": ["a"], "start": "zzz", "accept": [], "transitions": {}},
        {"states": ["a"], "start": "a", "accept": ["x"], "transitions": {}},
        {"states": ["a"], "start": "a", "accept": [], "transitions": {"a": {"0": "nope"}}},
    ]:
        try:
            Automaton.from_dict(bad)
        except ValueError:
            continue
        raise AssertionError(f"should have raised ValueError: {bad}")


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for t in tests:
        t()
        print(f"PASS  {t.__name__}")
    print(f"\nAll {len(tests)} tests passed.")