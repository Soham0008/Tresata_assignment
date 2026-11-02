"""Deterministic part: turns a nature-of-payment label into section, rate and amount.

Nothing in here is probabilistic. Every number comes from rules.json, the vendor
master or the year-to-date ledger, and every step is written to `steps` so that a
reviewer (or an auditor) can follow how the amount was reached.
"""

NO_PAN_FLOOR = 0.20


def payee_type(pan):
    """4th character of a PAN tells us who the holder is. P = individual, H = HUF."""
    if not pan or len(pan) != 10:
        return None
    return "individual_huf" if pan[3].upper() in ("P", "H") else "others"


def normal_rate(rule, ptype):
    rates = rule["rate"]
    if "all" in rates:
        return rates["all"]
    if ptype is None:  # unknown payee type: take the higher of the two
        return max(rates.values())
    return rates[ptype]


def crosses_threshold(th, base, ytd_paid):
    """Returns (crossed, catch_up_allowed, explanation)."""
    kind = th["type"]
    if kind == "single_or_aggregate":
        if ytd_paid + base > th["aggregate"]:
            return True, True, f"year-to-date {ytd_paid:,.0f} + this {base:,.0f} exceeds aggregate limit {th['aggregate']:,}"
        if base > th["single"]:
            return True, False, f"single payment {base:,.0f} exceeds {th['single']:,}"
        return False, False, f"single {base:,.0f} <= {th['single']:,} and year-to-date {ytd_paid + base:,.0f} <= {th['aggregate']:,}"
    if kind == "aggregate":
        total = ytd_paid + base
        if total > th["aggregate"]:
            return True, True, f"year-to-date {total:,.0f} exceeds {th['aggregate']:,}"
        return False, False, f"year-to-date {total:,.0f} <= {th['aggregate']:,}"
    if kind == "per_month":
        if base > th["per_month"]:
            return True, False, f"monthly amount {base:,.0f} exceeds {th['per_month']:,}"
        return False, False, f"monthly amount {base:,.0f} <= {th['per_month']:,}"
    raise ValueError(f"unknown threshold type {kind}")


def compute(nature, line, invoice, vendor_id, vendor, ledger, rules):
    out = {"nature": nature, "section": None, "base": None, "rate": None,
           "tds": None, "steps": [], "review": []}
    steps, review = out["steps"], out["review"]

    if not vendor.get("resident", True):
        review.append("Non-resident payee: s.195 / tax treaty applies, which is outside this tool")
        return out

    rule = rules["natures"].get(nature)
    if rule is None or nature == "unclear":
        review.append("Nature of payment could not be determined")
        return out

    if rule["section"] is None:
        out["tds"] = 0
        steps.append(f"'{nature}': no deduction under 194C/194J/194I/194H. {rule.get('note', '')}".strip())
        return out

    section = rule["section"]
    out["section"] = section

    # Base: GST excluded when shown separately (CBDT Circular 23/2017)
    if invoice["gst_shown_separately"]:
        base = line["amount"]
        steps.append(f"Base = {base:,.0f} (GST {line['gst']:,.0f} shown separately, excluded)")
    else:
        base = line["amount"] + line.get("gst", 0)
        steps.append(f"Base = {base:,.0f} (GST not shown separately)")
    out["base"] = base

    led = ledger.get(vendor_id, {}).get(section, {})
    ytd_paid = led.get("paid", 0)
    tds_started = led.get("tds_started", False)

    crossed, catch_up_ok, why = crosses_threshold(rule["threshold"], base, ytd_paid)
    if not crossed and not tds_started:
        out["tds"] = 0
        steps.append(f"Below threshold: {why}. Nothing to deduct now; amount added to year-to-date.")
        return out
    steps.append(f"Threshold: {why}" if crossed else "Deduction already started for this vendor/section this year")

    taxable = base
    if crossed and catch_up_ok and not tds_started and ytd_paid > 0:
        taxable = ytd_paid + base
        steps.append(f"Catch-up: earlier payments of {ytd_paid:,.0f} had no deduction, so deduct on {taxable:,.0f}")

    pan = vendor.get("pan")
    if rule.get("transporter_exemption") and vendor.get("transporter_declaration") and pan:
        out["tds"] = 0
        steps.append("s.194C(6): transporter declaration and PAN on file, no deduction")
        return out

    ptype = payee_type(pan)
    rate = normal_rate(rule, ptype)
    steps.append(f"Normal rate for {section}, payee type {ptype or 'unknown'}: {rate:.0%}")

    if not pan:
        rate = max(rate, 2 * rate, NO_PAN_FLOOR)
        steps.append(f"No PAN (s.206AA): rate raised to {rate:.0%}")
        review.append("No PAN on file: ask the vendor for PAN before deducting at 20%")

    cert = vendor.get("lower_deduction_cert")
    if cert and pan and cert["section"] == section and invoice["date"] <= cert["valid_to"]:
        remaining = cert["limit"] - led.get("cert_used", 0)
        if taxable <= remaining:
            rate = cert["rate"]
            steps.append(f"Lower-deduction certificate (s.197): {rate:.0%}, limit left {remaining:,.0f}")
        else:
            review.append(f"Lower-deduction certificate limit left ({remaining:,.0f}) is less than this payment")

    out["rate"] = rate
    out["tds"] = round(taxable * rate)
    steps.append(f"TDS = {taxable:,.0f} x {rate:.0%} = {out['tds']:,}")
    return out
