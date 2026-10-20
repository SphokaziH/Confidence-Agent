#!/usr/bin/env python3
"""
analyze_results.py - summarise the CSV written by run_experiment.py.

Usage:
    python analyze_results.py results.csv

Part A uses only the verifier's verdicts.
Part B uses the 'manual_correct' column: fill it with TRUE or FALSE by hand for a
sample of rows (ideally including some CORRECT and some INCORRECT verdicts and
some UNABLE_TO_VERIFY rows). It lets you measure false rejections and missed
hallucinations without relying on the verifier to mark itself.
"""

import csv
import math
import sys
from collections import Counter, defaultdict


def wilson(k, n, z=1.96):
    """95% Wilson score interval for a proportion k/n."""
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    d = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / d
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, centre - half), min(1.0, centre + half))


def pct(k, n):
    if n == 0:
        return "n/a"
    lo, hi = wilson(k, n)
    return f"{k}/{n} = {100 * k / n:.1f}%  (95% CI {100 * lo:.1f}% to {100 * hi:.1f}%)"


def mean(xs):
    xs = list(xs)
    return sum(xs) / len(xs) if xs else float("nan")


def to_float(s):
    try:
        return float(s)
    except (TypeError, ValueError):
        return None


def parse_bool(s):
    s = (s or "").strip().lower()
    if s in ("true", "yes", "1", "t", "y"):
        return True
    if s in ("false", "no", "0", "f", "n"):
        return False
    return None


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    with open(sys.argv[1], "r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))

    ok = [r for r in rows if not r["error"] and r["verdict"]]
    errors = [r for r in rows if r["error"]]
    print(f"Rows: {len(rows)}   usable: {len(ok)}   errors: {len(errors)}")
    models = sorted({r["model"] for r in rows})
    print(f"Model(s): {', '.join(models)}")
    print(f"Items: {len({r['item'] for r in rows})}   "
          f"runs per item (max): {max((int(r['run']) for r in rows), default=0)}")

    # ---------------- Part A: verifier verdicts ----------------
    print("\n=== A. Verifier verdicts ===")
    by_type = defaultdict(Counter)
    for r in ok:
        by_type[r["claim_type"]][r["verdict"]] += 1
    print(f"{'claim type':<14}{'CORRECT':>9}{'INCORRECT':>11}{'UNABLE':>8}")
    for t, c in sorted(by_type.items()):
        print(f"{t:<14}{c['CORRECT']:>9}{c['INCORRECT']:>11}{c['UNABLE_TO_VERIFY']:>8}")

    verifiable = [r for r in ok if r["verdict"] in ("CORRECT", "INCORRECT")]
    wrong = [r for r in verifiable if r["verdict"] == "INCORRECT"]
    print(f"\nCoverage (answers the verifier could check): {pct(len(verifiable), len(ok))}")
    print(f"Wrong among verifiable answers (baseline wrong rate): {pct(len(wrong), len(verifiable))}")
    print("Note: for checkable claims the verifier is also the source of truth, so its")
    print("detection of these errors is high by construction. Use Part B to test it.")

    c_ok = [to_float(r["confidence"]) for r in verifiable if r["verdict"] == "CORRECT"]
    c_bad = [to_float(r["confidence"]) for r in wrong]
    print(f"Mean confidence, CORRECT answers:   {mean(x for x in c_ok if x is not None):.3f}")
    print(f"Mean confidence, INCORRECT answers: {mean(x for x in c_bad if x is not None):.3f}")

    b = len(wrong)
    if b:
        p = min(1.0, 2 * 0.5 ** b)
        print(f"Exact sign/McNemar test (c = 0): b = {b}, two-sided p = {p:.4g}")
        print("  (b must be at least 6 for p < 0.05 when c = 0.)")

    lat_llm = [to_float(r["llm_seconds"]) for r in ok if to_float(r["llm_seconds"]) is not None]
    lat_ver = [to_float(r["verify_seconds"]) for r in ok if to_float(r["verify_seconds"]) is not None]
    if lat_llm:
        print(f"Mean latency: LLM {mean(lat_llm):.2f}s, verifier {mean(lat_ver):.4f}s")

    # Regex dialect effect
    rx = [r for r in ok if r["claim_type"] == "regex" and r["regex_textbook_verdict"]]
    if rx:
        diff = [r for r in rx if r["regex_textbook_verdict"] != r["verdict"]]
        print(f"\nRegex rows: {len(rx)}. Verdict changes when '+' is read as union: {len(diff)}")
        for r in diff[:10]:
            claim = r["claim_json"]
            print(f"  {r['item']} run {r['run']}: raw={r['verdict']}, textbook={r['regex_textbook_verdict']}  {claim}")

    # Per-item view
    print("\n=== Per item (verifiable runs only) ===")
    per_item = defaultdict(lambda: [0, 0, 0])  # wrong, verifiable, unverifiable
    for r in ok:
        if r["verdict"] == "UNABLE_TO_VERIFY":
            per_item[r["item"]][2] += 1
        else:
            per_item[r["item"]][1] += 1
            per_item[r["item"]][0] += r["verdict"] == "INCORRECT"
    for item in sorted(per_item, key=lambda s: int("".join(ch for ch in s if ch.isdigit()) or 0)):
        w, v, u = per_item[item]
        print(f"  {item:<16} wrong {w}/{v}   unverifiable {u}")

    # ---------------- Part B: manual audit ----------------
    audited = [(r, parse_bool(r["manual_correct"])) for r in ok if parse_bool(r["manual_correct"]) is not None]
    print(f"\n=== B. Manual audit ({len(audited)} rows with manual_correct filled) ===")
    if not audited:
        print("No audited rows. Fill 'manual_correct' with TRUE/FALSE for a sample to enable this part.")
        return

    cell = Counter()
    for r, truth in audited:
        flagged = r["verdict"] == "INCORRECT"
        accepted = r["verdict"] == "CORRECT"
        unable = r["verdict"] == "UNABLE_TO_VERIFY"
        cell[(truth, "flagged" if flagged else "accepted" if accepted else "unable")] += 1

    print(f"{'':<26}{'accepted':>10}{'flagged':>10}{'unable':>10}")
    for truth, label in ((True, "answer truly correct"), (False, "answer truly wrong")):
        print(f"{label:<26}{cell[(truth, 'accepted')]:>10}{cell[(truth, 'flagged')]:>10}{cell[(truth, 'unable')]:>10}")

    n = len(audited)
    n_wrong = sum(1 for _, t in audited if not t)
    n_right = n - n_wrong
    caught = cell[(False, "flagged")]
    missed = cell[(False, "accepted")] + cell[(False, "unable")]
    false_alarm = cell[(True, "flagged")]
    print(f"\nBaseline hallucination reach rate:  {pct(n_wrong, n)}")
    print(f"Agent reach rate (wrong & not flagged): {pct(missed, n)}")
    print(f"Detection rate (wrong answers flagged): {pct(caught, n_wrong)}")
    print(f"False-rejection rate (correct flagged): {pct(false_alarm, n_right)}")
    print("Small audited samples give wide intervals; say so in the report.")


if __name__ == "__main__":
    main()