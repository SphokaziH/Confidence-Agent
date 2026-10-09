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
class Verifier:
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

    # STRUCTURAL VERIFICATION
    def verify_structure(
        self,
        claim: Dict[str, Any]
    ) -> VerificationResult:
        """
        Verify structural claims about the automaton.
            eg.
            {
                "type": "DFA",
                "num_states": 3,
                "start": "q0"
            }
        """

        actual = self.automaton.summary() #ground truth structural information

        total_claims = 0
        correct_claims = 0

        evidence = []
        counterexamples = []

        for property_name, claimed_value in claim.items():

            # skip unknown properties
            if property_name not in actual:
                evidence.append(
                    f"Unknown structural property: {property_name}"
                )
                continue

            total_claims += 1

            actual_value = actual[property_name]

            if actual_value == claimed_value:

                correct_claims += 1

                evidence.append(
                    f"{property_name}: correct "
                    f"({actual_value})"
                )

            else:

                counterexamples.append(
                    f"{property_name}: "
                    f"claimed={claimed_value}, "
                    f"actual={actual_value}"
                )

        # calculate confidence
        if total_claims == 0:
            confidence = 0.0
        else:
            confidence = correct_claims / total_claims

        #decide final verdict
        if total_claims == 0:

            verdict = "UNABLE_TO_VERIFY"
            hallucination = False

        elif correct_claims == total_claims:

            verdict = "CORRECT"
            hallucination = False

        else:

            verdict = "INCORRECT"
            hallucination = True

        return VerificationResult(
            verdict=verdict,
            confidence=confidence,
            hallucination=hallucination,
            claim_type="structural",
            evidence=evidence,
            counterexamples=counterexamples,
            details={
                "claimed_properties": total_claims,
                "correct_properties": correct_claims,
                "actual_summary": actual
            }
        )

    # AUTOMATON EQUIVALENT
    def verify_equivalence(
        self,
        other: Automaton
    ) -> VerificationResult:
        """
        determine whether another automaton recognises exactly
        the same language as this automaton
        """

        difference = self.automaton.find_difference(other)

        if difference is None:

            return VerificationResult(
                verdict="CORRECT",
                confidence=1.0,
                hallucination=False,
                claim_type="equivalence",
                evidence=[
                    "The two automata recognise the same language.",
                    "No distinguishing string was found."
                ],
                details={
                    "equivalent": True
                }
            )

        else:

            return VerificationResult(
                verdict="INCORRECT",
                confidence=0.0,
                hallucination=True,
                claim_type="equivalence",
                evidence=[
                    "The two automata do not recognise the same language."
                ],
                counterexamples=[
                    f"Distinguishing string: '{difference}'"
                ],
                details={
                    "equivalent": False,
                    "difference": difference
                }
            )

    # SINGLE STRING VERIFICATION
    def verify_string(
        self,
        string: str,
        claimed_acceptance: bool
    ) -> VerificationResult:
        """
            verify a claim about one perticular string

            claimed_acceptance = True if the dfa accepts that string
        """

        actual_acceptance = self.automaton.accepts(string)

        if actual_acceptance == claimed_acceptance:

            verdict = "CORRECT"
            hallucination = False
            confidence = 1.0

            evidence = [
                f"Automaton result for '{string}': "
                f"{'ACCEPT' if actual_acceptance else 'REJECT'}",
                "This agrees with the claim."
            ]

            counterexamples = []

        else:

            verdict = "INCORRECT"
            hallucination = True
            confidence = 0.0

            evidence = [
                f"Automaton result for '{string}': "
                f"{'ACCEPT' if actual_acceptance else 'REJECT'}",
                "This contradicts the claim."
            ]

            counterexamples = [
                f"'{string}' is a counterexample."
            ]

        return VerificationResult(
            verdict=verdict,
            confidence=confidence,
            hallucination=hallucination,
            claim_type="string",
            evidence=evidence,
            counterexamples=counterexamples,
            details={
                "string": string,
                "claimed_acceptance": claimed_acceptance,
                "actual_acceptance": actual_acceptance
            }
        )

# -------------------Convenient Functions----------------
def verify_language(
    automaton: Automaton,
    claim: Callable[[str], bool],
    max_len: int = 6
) -> VerificationResult:
    """
    convenience function for semantic verification
    """

    verifier = Verifier(automaton)

    return verifier.verify_language_claim(
        claim,
        max_len
    )

def verify_regex(
    automaton: Automaton,
    pattern: str,
    max_len: int = 6
) -> VerificationResult:
    """
    convenience function for regex verification
    """

    verifier = Verifier(automaton)

    return verifier.verify_regex_claim(
        pattern,
        max_len
    )

def verify_structure(
    automaton: Automaton,
    claim: Dict[str, Any]
) -> VerificationResult:
    """
    convenience function for structural verification
    """

    verifier = Verifier(automaton)

    return verifier.verify_structure(claim)

def verify_equivalence(
    original: Automaton,
    other: Automaton
) -> VerificationResult:
    """
    convenience function for equivalence verification
    """

    verifier = Verifier(original)

    return verifier.verify_equivalence(other)

def verify_string(
    automaton: Automaton,
    string: str,
    claimed_acceptance: bool
) -> VerificationResult:
    """
    Convenience function for checking one string.
    """

    verifier = Verifier(automaton)

    return verifier.verify_string(
        string,
        claimed_acceptance
    )
