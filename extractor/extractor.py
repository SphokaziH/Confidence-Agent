import re


def extract_claim(question, response):
    """
    Extract a structured claim from an LLM response.

    Returns:
        claim_type, claim
    """

    question_lower = question.lower()
    response_lower = response.lower()


    # ---------------------------------
    # STRING ACCEPTANCE QUESTIONS
    # ---------------------------------

    if "accept" in question_lower or "reject" in question_lower:

        string_match = re.search(
            r"(?:string\s*)?[\"']([01]+)[\"']",
            question,
            re.IGNORECASE
        )


        if string_match:

            string_value = string_match.group(1)

            accepted = True


            if (
                "reject" in response_lower
                or "not accepted" in response_lower
                or "does not accept" in response_lower
            ):
                accepted = False


            return "string", {
                "string": string_value,
                "accepted": accepted
            }



    # ---------------------------------
    # REGEX QUESTIONS
    # ---------------------------------
    if (
        "regular expression" in question_lower
        or "regex" in question_lower
    ):

    # Try to find a regex inside the answer

        regex_match = re.search(
            r"(?:regex|regular expression)\s*(?:is|:|=)?\s*([01\+\*\?\|\(\)\[\]\.]+)",
            response,
            re.IGNORECASE
        )


        if regex_match:

            regex = regex_match.group(1).strip()


        else:

        # fallback: search for regex-like pattern
            regex_match = re.search(
                r"[01\(\)\+\*\?\|]+",
                response
            )


            if regex_match:
                regex = regex_match.group(0)
            else:
                regex = response.strip()


        return "regex", {
            "regex": regex
        }



    # ---------------------------------
    # STRUCTURAL QUESTIONS
    # ---------------------------------

    claim = {}



    # ---------------------------------
    # AUTOMATON TYPE
    # ---------------------------------

    if "dfa" in response_lower:

        claim["type"] = "DFA"


    elif "nfa" in response_lower:

        claim["type"] = "NFA"



    # ---------------------------------
    # STATES
    # Detect:
    # q0 q1 q2
    # A B C D
    # ---------------------------------

    states = sorted(
        set(
            re.findall(
                r"\b(?:q\d+|[A-Z])\b",
                response
            )
        )
    )


    if states:

        claim["states"] = states

        claim["num_states"] = len(states)



    # ---------------------------------
    # START STATE
    # ---------------------------------

    start = re.search(

        r"""
        start
        \s+
        state
        \s*
        (?:is|=|:)
        \s*
        ([A-Za-z0-9]+)
        """,

        response,

        re.IGNORECASE | re.VERBOSE
    )


    if start:

        claim["start"] = start.group(1)



    # ---------------------------------
    # ACCEPTING STATES
    # ---------------------------------

    accepting = re.search(

        r"""
        (?:
            accepting
            |
            accept
            |
            final
        )
        .*?
        (?:
            state
            |
            states
        )
        .*?
        (?:
            are
            |
            is
            |
            =
            |
            :
        )?
        \s*
        ([A-Za-z0-9,\s]+)
        """,

        response,

        re.IGNORECASE | re.VERBOSE
    )


    if accepting:


        accept_states = re.findall(

            r"(?:q\d+|[A-Z])",

            accepting.group(1)

        )


        if accept_states:

            claim["accepting"] = accept_states



    # ---------------------------------
    # TRANSITIONS (OPTIONAL)
    # ---------------------------------

    transitions = re.findall(

        r"""
        ([A-Za-z0-9]+)
        \s*
        -
        \s*
        ([01])
        \s*
        ->
        \s*
        ([A-Za-z0-9]+)
        """,

        response,

        re.VERBOSE
    )


    if transitions:


        claim["transitions"] = []


        for source, symbol, target in transitions:

            claim["transitions"].append(

                {
                    "from": source,
                    "symbol": symbol,
                    "to": target
                }

            )



    return "structure", claim