"""
simulator.py - Finite automaton simulator (DFA and NFA, with epsilon moves).

Part of the Confidence Agent project. This module is the "ground truth" engine:
It loads an automaton from the structured JSON format, runs strings through it, traces the path taken, generates test strings, and answers structural questions.
verifier.py uses it to check claims made by the foundational model.

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


    

