"""
verifier.py - Verification Judge for the Confidence Agent project.
this module recieves a claim made by a model (LLM) and checks those claims
against the simulator.

this module is responsible for:
    deciding whether a claim is correct
    calculating confidence
    collecting evidence
    identifying contradictions / possible hallucinations
    producing a final verification report
"""

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from simulator import Automaton, ClaimResult

#---------------- RESULTS CONTAINER ----------------------

@dataclass
class VerificationResult:
    """
    Stores the results/decision made by the verifier.
    """

    verdict: str
    confidence: float
    hallucination: bool
    claim_type: str

    evidence: List[str] = field(default_factory=list)

    counterexamples: List[Any] = field(default_factory=list)

    details: Dict[str, Any] = field(default_factory=dict)

    def pretty(self) -> str:
        """
        Produce a human-readable version of the verification result.
        """

        lines = []

        lines.append("=== VERIFICATION RESULT ===")
        lines.append(f"Claim type: {self.claim_type}")
        lines.append(f"Verdict: {self.verdict}")
        lines.append(f"Confidence: {self.confidence:.1%}")
        lines.append(
            f"Possible hallucination: "
            f"{'YES' if self.hallucination else 'NO'}"
        )

        if self.evidence:
            lines.append("")
            lines.append("Evidence:")

            for item in self.evidence:
                lines.append(f"  - {item}")

        if self.counterexamples:
            lines.append("")
            lines.append("Counterexamples:")

            for item in self.counterexamples:
                lines.append(f"  - {item}")

        return "\n".join(lines)


#---------------- VERIFIER ----------------------
class verifier:
    """
        the verifier receives an automaton and checks claims made by the LLM
    """
    def __init__(self, automaton : Automaton):
        self.automaton = automaton

    # Sematic Verification
    def verify_language_claim(
        self,
        claim: Callable[[str], bool],
        max_len: int = 6
    ) -> VerificationResult:
            """ verify a claim about the language recognised 
                by the automaton
            """

            # Ask the simulator to test the claim.
            result: ClaimResult = self.automaton.check_claim(
                claim,
                max_len=max_len
            )

            # The simulator gives us the agreement rate.
            confidence = result.agreement_rate

            evidence = [
                f"Tested {result.tested} strings.",
                f"{result.agreed} strings agreed with the claim."
            ]

            # If there are counterexamples, record them.
            counterexamples = []

            for string, automaton_accepts, claim_accepts in result.counterexamples:
                counterexamples.append(
                    f"'{string}' -> "
                    f"automaton={automaton_accepts}, "
                    f"claim={claim_accepts}"
                )

            # Decide whether the claim is correct.
            if result.consistent:

                verdict = "CORRECT"
                hallucination = False

                evidence.append(
                    "No counterexamples were found."
                )
            else:

                verdict = "INCORRECT"
                hallucination = True

                evidence.append(
                    f"Found {len(result.counterexamples)} "
                    f"counterexample(s)."
                )

            return VerificationResult(
                verdict=verdict,
                confidence=confidence,
                hallucination=hallucination,
                claim_type="semantic",
                evidence=evidence,
                counterexamples=counterexamples,
                details={
                    "tested": result.tested,
                    "agreed": result.agreed,
                    "agreement_rate": result.agreement_rate
                }
            )


    # REGEX VARIFICATION
    def verify_regex_claim(
        self,
        pattern: str,
        max_len: int = 6
    ) -> VerificationResult:
        """
        Verify a regular-expression description of the language.
        """

        result = self.automaton.check_claim_regex(
            pattern,
            max_len=max_len
        )

        confidence = result.agreement_rate

        evidence = [
            f"Regex tested: {pattern}",
            f"Tested {result.tested} strings.",
            f"{result.agreed} strings agreed with the regex."
        ]

        counterexamples = []

        for string, automaton_accepts, claim_accepts in result.counterexamples:

            counterexamples.append(
                f"'{string}' -> "
                f"automaton={automaton_accepts}, "
                f"regex={claim_accepts}"
            )

        if result.consistent:

            verdict = "CORRECT"
            hallucination = False

            evidence.append(
                "No counterexamples were found."
            )

        else:

            verdict = "INCORRECT"
            hallucination = True

            evidence.append(
                f"Found {len(result.counterexamples)} "
                f"counterexample(s)."
            )

        return VerificationResult(
            verdict=verdict,
            confidence=confidence,
            hallucination=hallucination,
            claim_type="regex",
            evidence=evidence,
            counterexamples=counterexamples,
            details={
                "pattern": pattern,
                "tested": result.tested,
                "agreed": result.agreed,
                "agreement_rate": result.agreement_rate
            }
        )