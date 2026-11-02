"""Glue: read -> check -> compute -> route, and write one audit record per line.

A line is auto-approved only if every check passes. Anything else goes to the
review queue with the reasons spelled out, so the reviewer starts from the
specific doubt instead of from scratch.
"""
import re

from .engine import compute
from .reader import NATURES, invoice_text

# Instructions or exemption claims addressed to whoever processes the invoice.
# Exemptions only ever come from the verified vendor master, never from invoice text.
INJECTION = re.compile(
    r"ignore (all |any )?(previous|prior|above) instructions|\b(ai|system|bot)\b[^.]{0,40}\b(classify|instruction)"
    r"|do not deduct|tds exemption|exempt from tds|no tds (is )?applicable",
    re.I)

REVIEW_IF_TDS_ABOVE = 100000  # materiality: big amounts always get a second look


def norm(s):
    return re.sub(r"\s+", " ", (s or "").lower()).strip()


def process(inv, vendor_id, vendor, ledger, rules, guidance, reader):
    text = invoice_text(inv, vendor)
    reading = reader(inv, vendor, rules, guidance)
    by_line = {r.get("line"): r for r in reading.get("lines", []) if isinstance(r, dict)}
    invoice_flags = []
    if INJECTION.search(text) or reading.get("injection_suspected"):
        invoice_flags.append("Invoice text contains instructions or an exemption claim; "
                             "exemptions are only taken from the vendor master")
    if reading.get("unreadable"):
        invoice_flags.append("Model reply could not be parsed")

    records = []
    for ln in inv["lines"]:
        r = by_line.get(ln["no"], {})
        nature = r.get("nature", "unclear")
        reasons = list(invoice_flags)

        # 1. Is the reading well-formed and grounded in the document?
        if nature not in NATURES:
            reasons.append(f"Reader returned an unknown label '{nature}'")
            nature = "unclear"
        ev = r.get("evidence", "")
        if nature != "unclear" and (not ev or norm(ev) not in norm(text)):
            reasons.append(f"Evidence quote not found in the invoice: '{ev}'")
        if r.get("confidence", "low") != "high":
            reasons.append(f"Reader confidence is {r.get('confidence', 'missing')}")
        retrieved = set(reading.get("retrieved", []))
        cited = set(r.get("guidance_used") or [])
        if retrieved and not cited <= retrieved:
            reasons.append(f"Cites guidance it was not given: {sorted(cited - retrieved)}")

        # 2. Exact computation from rules + master data
        calc = compute(nature, ln, inv, vendor_id, vendor, ledger, rules)
        reasons += calc["review"]

        # 3. Consistency checks
        alt = r.get("alternative")
        if alt and alt in rules["natures"] and alt != nature:
            alt_sec = rules["natures"][alt].get("section")
            if alt_sec != calc["section"]:
                reasons.append(f"Plausible alternative '{alt}' would mean section {alt_sec or 'none'}")
        hist = vendor.get("history_sections")
        if hist and calc["section"] and calc["section"] not in hist:
            reasons.append(f"Section {calc['section']} differs from this vendor's history {hist}")
        if calc["tds"] and calc["tds"] > REVIEW_IF_TDS_ABOVE:
            reasons.append("Large amount")

        records.append({
            "invoice": inv["id"], "line": ln["no"], "description": ln["description"],
            "nature": nature, "evidence": ev, "confidence": r.get("confidence"),
            "alternative": alt, "reader_reason": r.get("reason"),
            "guidance_used": sorted(cited), "guidance_retrieved": sorted(retrieved),
            "section": calc["section"], "base": calc["base"], "rate": calc["rate"], "tds": calc["tds"],
            "steps": calc["steps"], "route": "review" if reasons else "auto", "review_reasons": reasons,
            "rule_version": rules["rule_version"], "model": reading.get("model", "-"),
        })
    return records
