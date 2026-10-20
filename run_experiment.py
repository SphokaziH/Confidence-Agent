#!/usr/bin/env python3
"""
run_experiment.py - batch runner for the Confident Agent experiment.

Runs every benchmark item that has an automaton JSON file (Diagram1..Diagram28)
through the LLM several times, then runs the verifier on each stored response
and writes one CSV row per (item, run).

Why one CSV serves both conditions
  * Baseline  = the stored LLM answer with no verifier (every answer reaches the user).
  * Agent     = the same stored answer plus the verifier's verdict.
  Scoring both on the same response removes LLM variation from the comparison.

Usage (run from the repository root, next to main.py):
    python run_experiment.py                       # 5 runs per item, real Gemini calls
    python run_experiment.py --runs 3 --sleep 2    # fewer runs, slower pace
    python run_experiment.py --items 1 5 14        # only some items
    python run_experiment.py --dry-run --runs 2    # no API calls, tests the pipeline
    python run_experiment.py --out results.csv     # resumes if the file already exists

Needs GEMINI_API_KEY in .env for real runs (not for --dry-run).
"""

import argparse
import copy
import csv
import datetime
import json
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from verifier.simulator import Automaton  # noqa: E402
from verifier.verifier import Verifier  # noqa: E402

BENCH = ROOT / "Benchmark"
JSON_DIR = BENCH / "JSON files"
QUESTIONS = BENCH / "questions.json"

# Spellings of epsilon that must not count as alphabet letters.
EPS_ALIASES = {"", "ε", "eps", "epsilon", "λ", "lambda"}

FIELDS = [
    "timestamp", "model", "item", "run", "question",
    "claim_type", "claim_json", "answer",
    "verdict", "confidence", "hallucination_flag", "evidence", "counterexamples",
    "regex_textbook_verdict", "regex_textbook_confidence", "regex_textbook_counterexamples",
    "llm_seconds", "verify_seconds", "error",
    "manual_correct",  # leave blank; fill TRUE/FALSE by hand for the audit sample
]


# ----------------------------------------------------------------------------
# Loading the benchmark
# ----------------------------------------------------------------------------
def item_number(name):
    m = re.search(r"(\d+)", name)
    return int(m.group(1)) if m else 10**9


def load_items(only=None):
    """Return [(item_id, question, automaton_dict)] for items that have a JSON file."""
    with open(QUESTIONS, "r", encoding="utf-8") as f:
        questions = json.load(f)

    items = []
    for path in sorted(JSON_DIR.glob("*.json"), key=lambda p: item_number(p.name)):
        item_id = path.name
        n = item_number(item_id)
        if only and n not in only:
            continue
        if item_id not in questions:
            print(f"warning: no question for {item_id}, skipped", file=sys.stderr)
            continue
        with open(path, "r", encoding="utf-8") as f:
            automaton = json.load(f)
        items.append((item_id, questions[item_id][0], automaton))
    return items


def clean_for_verifier(data):
    """
    Copy of the automaton with epsilon spellings removed from the alphabet.
    Several benchmark files list 'epsilon' as an alphabet symbol, which makes the
    simulator generate test strings containing the literal word 'epsilon'.
    The LLM still receives the original, unmodified JSON.
    """
    data = copy.deepcopy(data)
    inner = data.get("automaton", data)
    if isinstance(inner.get("alphabet"), list):
        inner["alphabet"] = [s for s in inner["alphabet"] if s not in EPS_ALIASES]
    return data


def textbook_to_python(pattern):
    """
    Convert textbook regex notation to Python syntax. ASSUMES '+' means union,
    which is wrong if the model used Python's one-or-more '+'. Both verdicts
    are stored so you can decide which reading applies.
    """
    p = pattern.replace(" ", "")
    p = p.replace("∪", "|").replace("+", "|")
    p = p.replace("ε", "()").replace("∅", "(?!)")
    return p


# ----------------------------------------------------------------------------
# LLM access
# ----------------------------------------------------------------------------
def fake_response(automaton, run):
    """Dry-run stand-in for Gemini: a structure claim, wrong on every second run."""
    s = Automaton.from_dict(clean_for_verifier(automaton)).summary()
    claim = {"type": s["type"], "start": s["start"], "accepting": s["accepting"]}
    if run % 2 == 0:
        claim["start"] = "WRONG"
    return json.dumps({"answer": "dry-run answer", "claim_type": "structure", "claim": claim})


def call_with_retry(fn, attempts=4, base_delay=5.0):
    last = None
    for i in range(attempts):
        try:
            return fn()
        except Exception as exc:  # network, quota, rate limit...
            last = exc
            if i < attempts - 1:
                delay = base_delay * (2 ** i)
                print(f"    LLM call failed ({exc}); retrying in {delay:.0f}s", file=sys.stderr)
                time.sleep(delay)
    raise last


# ----------------------------------------------------------------------------
# One experimental unit
# ----------------------------------------------------------------------------
def run_one(item_id, question, automaton, run, generate, model_name):
    row = {k: "" for k in FIELDS}
    row.update(
        timestamp=datetime.datetime.now().isoformat(timespec="seconds"),
        model=model_name, item=item_id, run=run, question=question,
    )

    # 1. LLM call
    t0 = time.perf_counter()
    try:
        raw = call_with_retry(lambda: generate(question, automaton, run))
    except Exception as exc:
        row["error"] = f"LLM: {exc}"
        return row
    row["llm_seconds"] = f"{time.perf_counter() - t0:.3f}"

    try:
        data = json.loads(raw)
        row["answer"] = data.get("answer", "")
        row["claim_type"] = data.get("claim_type", "")
        row["claim_json"] = json.dumps(data.get("claim", {}), ensure_ascii=False)
    except Exception:
        row["answer"] = str(raw)
        row["claim_type"] = "unparseable"

    # 2. Verification
    t1 = time.perf_counter()
    try:
        verifier = Verifier(Automaton.from_dict(clean_for_verifier(automaton)))
        res = verifier.verify_llm_response(raw)
        row["verdict"] = res.verdict
        row["confidence"] = f"{res.confidence:.4f}"
        row["hallucination_flag"] = res.hallucination
        row["evidence"] = " | ".join(res.evidence)
        row["counterexamples"] = " | ".join(res.counterexamples[:10])

        # Extra: regex checked again under textbook notation (+ as union)
        if row["claim_type"] == "regex":
            pattern = json.loads(row["claim_json"]).get("regex")
            if isinstance(pattern, str):
                try:
                    alt = verifier.verify_regex_claim(textbook_to_python(pattern))
                    row["regex_textbook_verdict"] = alt.verdict
                    row["regex_textbook_confidence"] = f"{alt.confidence:.4f}"
                    row["regex_textbook_counterexamples"] = " | ".join(alt.counterexamples[:10])
                except re.error as exc:
                    row["regex_textbook_verdict"] = "UNABLE_TO_VERIFY"
                    row["regex_textbook_counterexamples"] = f"invalid after conversion: {exc}"
    except Exception as exc:
        row["error"] = f"VERIFY: {exc}"
    row["verify_seconds"] = f"{time.perf_counter() - t1:.4f}"
    return row


# ----------------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------------
def already_done(path):
    done = set()
    if path.exists():
        with open(path, "r", encoding="utf-8-sig", newline="") as f:
            for r in csv.DictReader(f):
                if r.get("error") == "" and r.get("item"):
                    done.add((r["item"], int(r["run"])))
    return done


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--runs", type=int, default=5, help="runs per item (default 5)")
    ap.add_argument("--items", type=int, nargs="*", help="only these item numbers, e.g. 1 5 14")
    ap.add_argument("--out", default="results.csv", help="output CSV (resumes if it exists)")
    ap.add_argument("--sleep", type=float, default=1.0, help="seconds between API calls")
    ap.add_argument("--dry-run", action="store_true", help="fake LLM, no API calls")
    args = ap.parse_args()

    out = Path(args.out)
    items = load_items(set(args.items) if args.items else None)
    if not items:
        sys.exit("No benchmark items found. Run this from the repository root.")

    if args.dry_run:
        model_name = "DRY-RUN"
        generate = lambda q, a, run: fake_response(a, run)
    else:
        try:
            import llm.llm as llm_mod
        except Exception as exc:
            sys.exit(f"Could not load llm/llm.py ({exc}).\n"
                     "Check that GEMINI_API_KEY is in your .env file and the libraries are installed.")
        model_name = getattr(getattr(llm_mod, "model", None), "model_name", "unknown")
        generate = lambda q, a, run: llm_mod.generate_response(q, a)

    done = already_done(out)
    new_file = not out.exists()
    total = len(items) * args.runs
    count = 0

    # utf-8-sig on creation so Excel shows symbols correctly; plain utf-8 when appending.
    with open(out, "w" if new_file else "a", encoding="utf-8-sig" if new_file else "utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        if new_file:
            writer.writeheader()

        for item_id, question, automaton in items:
            for run in range(1, args.runs + 1):
                count += 1
                if (item_id, run) in done:
                    print(f"[{count}/{total}] {item_id} run {run}: already done, skipped")
                    continue
                row = run_one(item_id, question, automaton, run, generate, model_name)
                writer.writerow(row)
                f.flush()
                status = row["error"] or f"{row['claim_type']} -> {row['verdict']} ({row['confidence']})"
                print(f"[{count}/{total}] {item_id} run {run}: {status}")
                if not args.dry_run:
                    time.sleep(args.sleep)

    print(f"\nDone. Results in {out}. Next: python analyze_results.py {out}")


if __name__ == "__main__":
    main()