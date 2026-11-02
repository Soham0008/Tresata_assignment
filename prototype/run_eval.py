"""Run the test invoices through the pipeline and score the result.

    python run_eval.py --reader oracle     # engine alone, reader replaced by the right answer
    python run_eval.py --reader keywords   # non-AI baseline
    python run_eval.py --reader llm        # needs OPENROUTER_API_KEY

Writes results/<reader>.md (table) and results/<reader>_audit.json (full audit trail).

Verdicts per line:
  OK            right amount, routed as expected
  EXTRA REVIEW  right amount, but sent to a human when it didn't need to be (costs time, not money)
  CAUGHT        wrong reading, but it went to a human, so no harm done
  MISSED REVIEW right amount, but a case that needed a human went straight through
  SILENT ERROR  wrong amount and auto-approved - the one that actually costs money
"""
import argparse
import json
import os
from collections import Counter

from tds.pipeline import process
from tds.reader import READERS
from tds.retrieval import Guidance

HERE = os.path.dirname(os.path.abspath(__file__))


def load(name):
    with open(os.path.join(HERE, name)) as f:
        return json.load(f)


def verdict(case, exp, rec):
    ok_nature = (exp["nature"] == "any" or rec["nature"] == exp["nature"]
                 or rec["nature"] in case.get("accept_natures", []))
    ok_amount = exp["tds"] is None or rec["tds"] == exp["tds"]
    reviewed = rec["route"] == "review"
    if case.get("ambiguous"):
        if reviewed:
            return "OK"
        return "MISSED REVIEW" if ok_nature else "SILENT ERROR"
    if exp["route"] == "review":
        if reviewed:
            return "OK" if ok_amount else "CAUGHT"
        return "MISSED REVIEW" if ok_amount else "SILENT ERROR"
    if ok_amount:
        return "EXTRA REVIEW" if (reviewed and exp["route"] == "auto") else "OK"
    return "CAUGHT" if reviewed else "SILENT ERROR"


def fmt(v):
    return "-" if v is None else f"{v:,}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reader", choices=READERS, default="keywords")
    ap.add_argument("--only", help="run a single case id, e.g. C05")
    args = ap.parse_args()

    rules = load("data/rules.json")
    vendors = load("data/vendors.json")
    ledger = load("data/ledger_ytd.json")
    guidance = Guidance(load("data/guidance.json"))
    cases = load("tests/cases.json")
    if args.only:
        cases = [c for c in cases if c["id"] == args.only]

    rows, audit, tally = [], [], {"dev": Counter(), "heldout": Counter()}
    for case in cases:
        print(f"{case['id']}: {case['tests']}")
        vendor = vendors[case["vendor_id"]]
        recs = process(case, case["vendor_id"], vendor, ledger, rules, guidance, READERS[args.reader])
        for exp, rec in zip(case["expected"], recs):
            v = verdict(case, exp, rec)
            rec["expected"] = exp
            rec["verdict"] = v
            tally[case["set"]][v] += 1
            audit.append(rec)
            rows.append(f"| {case['id']}.{rec['line']} | {exp['nature']} / {fmt(exp['tds'])} | "
                        f"{rec['nature']} -> {rec['section'] or '-'} / {fmt(rec['tds'])} | {rec['route']} | "
                        f"**{v}** | {'; '.join(rec['review_reasons'])[:160]} |")
            print(f"   line {rec['line']}: {rec['nature']:<22} {str(rec['section']):<8} tds={fmt(rec['tds']):>7} "
                  f"{rec['route']:<6} {v}")

    lines_total = sum(sum(t.values()) for t in tally.values())
    all_t = tally["dev"] + tally["heldout"]
    auto = sum(1 for r in audit if r["route"] == "auto")
    summary = [f"# Results - reader: `{args.reader}`", "",
               f"Rule version `{rules['rule_version']}`. {len(cases)} invoices, {lines_total} lines.", "",
               "| Verdict | Dev set | Held-out set | Total |", "|---|---|---|---|"]
    for v in ["OK", "EXTRA REVIEW", "CAUGHT", "MISSED REVIEW", "SILENT ERROR"]:
        summary.append(f"| {v} | {tally['dev'][v]} | {tally['heldout'][v]} | {all_t[v]} |")
    summary += ["", f"Auto-approved: {auto} of {lines_total} lines. "
                    f"Silent errors: {all_t['SILENT ERROR']}.", "",
                "| Line | Expected nature / TDS | Got | Route | Verdict | Review reasons |",
                "|---|---|---|---|---|---|"] + rows

    os.makedirs(os.path.join(HERE, "results"), exist_ok=True)
    suffix = f"_{args.only}" if args.only else ""
    with open(os.path.join(HERE, "results", f"{args.reader}{suffix}.md"), "w") as f:
        f.write("\n".join(summary) + "\n")
    with open(os.path.join(HERE, "results", f"{args.reader}{suffix}_audit.json"), "w") as f:
        json.dump(audit, f, indent=1, ensure_ascii=False)
    print("\n" + "\n".join(summary[4:12]))
    print(f"\nWritten to results/{args.reader}{suffix}.md")


if __name__ == "__main__":
    main()
