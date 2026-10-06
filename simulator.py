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
