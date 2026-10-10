"""
simulator.py - Finite automaton simulator (DFA and NFA, with epsilon moves).

Part of the Confidence Agent project. This module is the "ground truth" engine:
it loads an automaton from the structured JSON format, runs strings through it,
traces the path taken, generates test strings, and answers structural questions.
verifier.py uses it to check claims made by the foundation model.

JSON format (NFA targets may be a list; epsilon key may be "", "eps", "ε"):

{
  "states": ["q0", "q1", "q2"],
  "alphabet": ["0", "1"],            # optional, inferred if missing
  "start": "q0",
  "accept": ["q2"],
  "transitions": {
      "q0": {"0": "q1", "1": "q0"},
      "q1": {"0": "q1", "1": "q2"},
      "q2": {"0": "q1", "1": "q0"}
  }
}
"""

from __future__ import annotations

import itertools
import json
import random
from collections import deque
from dataclasses import dataclass, field
from typing import Callable, Dict, FrozenSet, Iterable, List, Optional, Set, Tuple

EPSILON = "ε"
_EPSILON_ALIASES = {"", "ε", "eps", "epsilon", "λ", "lambda"}


#RESULT CONTAINTERS
@dataclass
class TraceStep:
    """One symbol consumed. For a DFA, from_states/to_states hold one state each."""
    symbol: str
    from_states: FrozenSet[str]
    to_states: FrozenSet[str]


@dataclass
class TraceResult:
    string: str
    accepted: bool
    steps: List[TraceStep] = field(default_factory=list)
    initial_states: FrozenSet[str] = frozenset()
    final_states: FrozenSet[str] = frozenset()
    reason: str = ""

    def pretty(self) -> str:
        def fmt(s: FrozenSet[str]) -> str:
            return "{" + ", ".join(sorted(s)) + "}" if s else "{}"
        lines = [f"Input: '{self.string}'", f"Start: {fmt(self.initial_states)}"]
        for st in self.steps:
            lines.append(f"  {fmt(st.from_states)} --{st.symbol}--> {fmt(st.to_states)}")
        lines.append(f"Result: {'ACCEPT' if self.accepted else 'REJECT'} ({self.reason})")
        return "\n".join(lines)


@dataclass
class ClaimResult:
    """Outcome of comparing a claimed language (predicate) against the automaton."""
    tested: int
    agreed: int
    counterexamples: List[Tuple[str, bool, bool]] = field(default_factory=list)
    # each counterexample: (string, automaton_accepts, claim_says_accepts)

    @property
    def agreement_rate(self) -> float:
        return self.agreed / self.tested if self.tested else 1.0

    @property
    def consistent(self) -> bool:
        return not self.counterexamples


#AUTOMATON
class Automaton:
    """A DFA or NFA (with optional epsilon transitions)."""

    def __init__(
        self,
        states: Iterable[str],
        start: str,
        accept: Iterable[str],
        transitions: Dict[str, Dict[str, object]],
        alphabet: Optional[Iterable[str]] = None,
    ):
        self.states: Set[str] = set(states)
        self.start: str = start
        self.accept: Set[str] = set(accept)
        self.delta: Dict[str, Dict[str, Set[str]]] = self._normalise(transitions)

        inferred = {sym for row in self.delta.values() for sym in row if sym != EPSILON}
        self.alphabet: List[str] = sorted(set(alphabet) if alphabet else inferred)

        self._validate()

    #CONSTRUCTION
    @staticmethod
    def _normalise(transitions: Dict[str, Dict[str, object]]) -> Dict[str, Dict[str, Set[str]]]:
        delta: Dict[str, Dict[str, Set[str]]] = {}
        for state, row in transitions.items():
            delta[state] = {}
            for sym, target in row.items():
                key = EPSILON if sym in _EPSILON_ALIASES else sym
                targets = set(target) if isinstance(target, (list, tuple, set)) else {target}
                delta[state].setdefault(key, set()).update(targets)
        return delta

    def _validate(self) -> None:
        if self.start not in self.states:
            raise ValueError(f"Start state '{self.start}' is not in the state set")
        bad_accept = self.accept - self.states
        if bad_accept:
            raise ValueError(f"Accepting states not in state set: {sorted(bad_accept)}")
        for src, row in self.delta.items():
            if src not in self.states:
                raise ValueError(f"Transition from unknown state '{src}'")
            for sym, targets in row.items():
                if sym != EPSILON and self.alphabet and sym not in self.alphabet:
                    raise ValueError(f"Symbol '{sym}' on '{src}' is not in the alphabet")
                unknown = targets - self.states
                if unknown:
                    raise ValueError(f"Transition {src} --{sym}--> unknown state(s) {sorted(unknown)}")

    @classmethod
    def from_dict(cls, data: dict) -> "Automaton":
        return cls(
            states=data["states"],
            start=data["start"],
            accept=data.get("accept", data.get("accepting", [])),
            transitions=data.get("transitions", {}),
            alphabet=data.get("alphabet"),
        )

    @classmethod
    def from_json(cls, path: str) -> "Automaton":
        with open(path, "r", encoding="utf-8") as f:
            return cls.from_dict(json.load(f))

    def to_dict(self) -> dict:
        return {
            "states": sorted(self.states),
            "alphabet": self.alphabet,
            "start": self.start,
            "accept": sorted(self.accept),
            "transitions": {
                s: {sym: sorted(t) for sym, t in row.items()}
                for s, row in sorted(self.delta.items())
            },
        }

    #CORE SIMULATION
    def epsilon_closure(self, states: Iterable[str]) -> FrozenSet[str]:
        closure = set(states)
        stack = list(closure)
        while stack:
            s = stack.pop()
            for t in self.delta.get(s, {}).get(EPSILON, ()):
                if t not in closure:
                    closure.add(t)
                    stack.append(t)
        return frozenset(closure)

    def step(self, states: Iterable[str], symbol: str) -> FrozenSet[str]:
        """All states reachable from `states` by reading `symbol` (then epsilon closure)."""
        nxt: Set[str] = set()
        for s in states:
            nxt.update(self.delta.get(s, {}).get(symbol, ()))
        return self.epsilon_closure(nxt)

    def accepts(self, string: str) -> bool:
        current = self.epsilon_closure({self.start})
        for ch in string:
            current = self.step(current, ch)
            if not current:          # dead: no way to continue
                return False
        return bool(current & self.accept)

    def trace(self, string: str) -> TraceResult:
        """Step-by-step run, useful for showing the user why a string is accepted/rejected."""
        current = self.epsilon_closure({self.start})
        result = TraceResult(string=string, accepted=False, initial_states=current)
        for ch in string:
            if ch not in self.alphabet:
                result.final_states = frozenset()
                result.reason = f"symbol '{ch}' is not in the alphabet {self.alphabet}"
                return result
            nxt = self.step(current, ch)
            result.steps.append(TraceStep(ch, current, nxt))
            current = nxt
            if not current:
                result.final_states = current
                result.reason = f"no transition on '{ch}' (dead end)"
                return result
        result.final_states = current
        result.accepted = bool(current & self.accept)
        result.reason = (
            "ended in accepting state(s) " + str(sorted(current & self.accept))
            if result.accepted
            else "ended in non-accepting state(s) " + str(sorted(current))
        )
        return result

    # STRUCTURAL PROPERTIES (for Structural Verification)
    def has_epsilon_transitions(self) -> bool:
        return any(EPSILON in row for row in self.delta.values())

    def is_deterministic(self) -> bool:
        if self.has_epsilon_transitions():
            return False
        return all(len(t) <= 1 for row in self.delta.values() for t in row.values())

    def is_complete(self) -> bool:
        return not self.missing_transitions()

    def missing_transitions(self) -> List[Tuple[str, str]]:
        """(state, symbol) pairs with no outgoing transition."""
        return [
            (s, a)
            for s in sorted(self.states)
            for a in self.alphabet
            if not self.delta.get(s, {}).get(a)
        ]

    def self_loops(self) -> List[Tuple[str, str]]:
        return [
            (s, sym)
            for s, row in sorted(self.delta.items())
            for sym, targets in sorted(row.items())
            if s in targets
        ]

    def reachable_states(self) -> Set[str]:
        seen = {self.start}
        queue = deque([self.start])
        while queue:
            s = queue.popleft()
            for targets in self.delta.get(s, {}).values():
                for t in targets:
                    if t not in seen:
                        seen.add(t)
                        queue.append(t)
        return seen

    def summary(self) -> dict:
        """Facts about the automaton, to compare against the model's visual/structural claims."""
        return {
            "num_states": len(self.states),
            "states": sorted(self.states),
            "alphabet": self.alphabet,
            "start": self.start,
            "accepting": sorted(self.accept),
            "type": "DFA" if self.is_deterministic() else "NFA",
            "complete": self.is_complete(),
            "missing_transitions": self.missing_transitions(),
            "has_epsilon": self.has_epsilon_transitions(),
            "self_loops": self.self_loops(),
            "unreachable_states": sorted(self.states - self.reachable_states()),
            "num_transitions": sum(len(t) for row in self.delta.values() for t in row.values()),
        }

    # TEST STRING GENERATION (for Semantic Verification) 
    def all_strings(self, max_len: int) -> Iterable[str]:
        """Every string over the alphabet up to max_len, shortest first (includes '')."""
        for n in range(max_len + 1):
            for combo in itertools.product(self.alphabet, repeat=n):
                yield "".join(combo)

    def accepted_strings(self, max_len: int, limit: Optional[int] = None) -> List[str]:
        out = [s for s in self.all_strings(max_len) if self.accepts(s)]
        return out[:limit] if limit else out

    def rejected_strings(self, max_len: int, limit: Optional[int] = None) -> List[str]:
        out = [s for s in self.all_strings(max_len) if not self.accepts(s)]
        return out[:limit] if limit else out

    def generate_test_strings(
        self, n: int = 20, max_len: int = 6, seed: Optional[int] = 0
    ) -> List[str]:
        """
        A balanced test set: always includes '' and the shortest accepted / rejected
        strings, then fills with a mix of accepted and rejected strings (random longer ones
        when the alphabet is large). Deterministic for a given seed so results are reproducible.
        """
        rng = random.Random(seed)
        pool = list(self.all_strings(max_len)) if len(self.alphabet) ** max_len <= 50_000 else []
        if not pool:  # large alphabet: sample instead of enumerating
            pool = [
                "".join(rng.choice(self.alphabet) for _ in range(rng.randint(0, max_len)))
                for _ in range(5000)
            ]
        acc = [s for s in pool if self.accepts(s)]
        rej = [s for s in pool if not self.accepts(s)]

        chosen: List[str] = []
        seen: Set[str] = set()

        def add(s: str) -> None:
            if s not in seen and len(chosen) < n:
                seen.add(s)
                chosen.append(s)

        add("")
        for s in acc[: max(1, n // 4)]:      # shortest accepted
            add(s)
        for s in rej[: max(1, n // 4)]:      # shortest rejected
            add(s)
        rest_acc, rest_rej = acc[:], rej[:]
        rng.shuffle(rest_acc)
        rng.shuffle(rest_rej)
        for a, r in itertools.zip_longest(rest_acc, rest_rej):
            if a is not None:
                add(a)
            if r is not None:
                add(r)
            if len(chosen) >= n:
                break
        return chosen

    #   CHECKING A CLAIM ABOUT THE LANGUAGE (for Semantic Verification)
    def check_claim(
        self,
        claim: Callable[[str], bool],
        strings: Optional[Iterable[str]] = None,
        max_len: int = 6,
    ) -> ClaimResult:
        """
        Compare a claimed language (a function string -> bool, e.g. lambda s: s.endswith("01"))
        against what the automaton really does. Any disagreement is a counterexample.
        """
        tests = list(strings) if strings is not None else list(self.all_strings(max_len))
        agreed = 0
        counter: List[Tuple[str, bool, bool]] = []
        for s in tests:
            real, claimed = self.accepts(s), bool(claim(s))
            if real == claimed:
                agreed += 1
            else:
                counter.append((s, real, claimed))
        return ClaimResult(tested=len(tests), agreed=agreed, counterexamples=counter)

    def check_claim_regex(self, pattern: str, strings: Optional[Iterable[str]] = None,
                          max_len: int = 6) -> ClaimResult:
        """Same as check_claim, but the claim is a regular expression (full-string match)."""
        import re
        rx = re.compile(pattern)
        return self.check_claim(lambda s: rx.fullmatch(s) is not None, strings, max_len)

    #EXACT COMPARISON WITH ANOTHER AUTOMATON 
    def to_dfa(self) -> "Automaton":
        """Subset construction. Result is a complete DFA over the same alphabet."""
        start = self.epsilon_closure({self.start})
        names: Dict[FrozenSet[str], str] = {}

        def name(fs: FrozenSet[str]) -> str:
            if fs not in names:
                names[fs] = "{" + ",".join(sorted(fs)) + "}" if fs else "∅"
            return names[fs]

        trans: Dict[str, Dict[str, str]] = {}
        accept: Set[str] = set()
        queue, seen = deque([start]), {start}
        while queue:
            cur = queue.popleft()
            n = name(cur)
            if cur & self.accept:
                accept.add(n)
            trans[n] = {}
            for a in self.alphabet:
                nxt = self.step(cur, a)
                trans[n][a] = name(nxt)
                if nxt not in seen:
                    seen.add(nxt)
                    queue.append(nxt)
        return Automaton(set(trans), name(start), accept, trans, self.alphabet)

    def find_difference(self, other: "Automaton") -> Optional[str]:
        """
        Shortest string accepted by exactly one of the two automata, or None if they
        recognise the same language. Exact (not sampled) - uses product BFS over DFAs.
        """
        a, b = self.to_dfa(), other.to_dfa()
        alphabet = sorted(set(a.alphabet) | set(b.alphabet))
        start = (a.start, b.start)
        queue = deque([(start, "")])
        seen = {start}
        while queue:
            (sa, sb), word = queue.popleft()
            if (sa in a.accept) != (sb in b.accept):
                return word
            for sym in alphabet:
                ta = next(iter(a.delta.get(sa, {}).get(sym, {"∅"})))
                tb = next(iter(b.delta.get(sb, {}).get(sym, {"∅"})))
                pair = (ta, tb)
                if pair not in seen:
                    seen.add(pair)
                    queue.append((pair, word + sym))
        return None

    def is_equivalent(self, other: "Automaton") -> bool:
        return self.find_difference(other) is None


#CONVENIENCE FUNCTIONS
def load_automaton(path: str) -> Automaton:
    return Automaton.from_json(path)


def simulate(automaton: Automaton, string: str) -> bool:
    """True if the automaton accepts `string`."""
    return automaton.accepts(string)


# DEMO / SELF-TEST:  python simulator.py [automaton.json]
if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        auto = load_automaton(sys.argv[1])
    else:
        # DFA for "binary strings ending in 01"
        auto = Automaton.from_dict({
            "states": ["q0", "q1", "q2"],
            "start": "q0",
            "accept": ["q2"],
            "transitions": {
                "q0": {"0": "q1", "1": "q0"},
                "q1": {"0": "q1", "1": "q2"},
                "q2": {"0": "q1", "1": "q0"},
            },
        })

    print("Summary:", json.dumps(auto.summary(), indent=2, ensure_ascii=False))
    print()
    print(auto.trace("1001").pretty())
    print()
    tests = auto.generate_test_strings(n=10, max_len=5)
    for s in tests:
        print(f"{s or '(empty)':>8} -> {'ACCEPT' if auto.accepts(s) else 'REJECT'}")

    print()
    good = auto.check_claim(lambda s: s.endswith("01"))
    bad = auto.check_claim(lambda s: s.endswith("10"))
    print(f"Claim 'ends in 01': agreement {good.agreement_rate:.0%}, consistent={good.consistent}")
    print(f"Claim 'ends in 10': agreement {bad.agreement_rate:.0%}, "
          f"first counterexample={bad.counterexamples[0] if bad.counterexamples else None}")