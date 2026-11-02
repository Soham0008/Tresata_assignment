# Getting the TDS section right on every vendor invoice

Indian companies have to deduct tax at source (TDS) when they pay vendors for services, rent or
commission. The rate depends on *what* the payment is for: contract work, professional or technical
fees, rent of a building or a machine, commission, and so on. Accounts-payable clerks make that call
on every invoice line, and mistakes cost interest and disallowed expenses months later.

The design splits the problem in two. An AI model reads each line and picks **what it is paying for**
from a fixed list, quoting the exact words it relied on. Plain code then works out **section, rate and
amount** from a versioned rule table. Anything doubtful goes to a person. Every line gets an audit record.

| What | Where |
|---|---|
| Written brief (4 pages incl. appendix) | [`Soham_Patil_2023AM11045_Tresata_Brief.pdf`](Soham_Patil_2023AM11045_Tresata_Brief.pdf) |
| Prototype, how to run it, test cases and results | [`prototype/README.md`](prototype/README.md) |

Quick start (Python 3.9+, no libraries):

```bash
cd prototype
python run_eval.py --reader keywords
```

All invoices, vendors and PANs are synthetic. Jurisdiction: India, resident vendors only.

## File guide

| Path | What it is |
|---|---|
| `Soham_Patil_2023AM11045_Tresata_Brief.pdf` | The submission PDF |
| `brief/brief.html` | Source text of the brief and appendix |
| `brief/build_pdf.js` | Turns `brief.html` into the PDF |
| `prototype/README.md` | How to run the prototype, test list, results |
| `prototype/run_eval.py` | Runs all test invoices and scores them |
| `prototype/tds/reader.py` | The only AI step (prompt and model call) |
| `prototype/tds/engine.py` | Section / rate / threshold / amount maths |
| `prototype/tds/pipeline.py` | Review checks and routing |
| `prototype/tds/retrieval.py` | Finds the relevant guidance notes |
| `prototype/data/rules.json` | Rates, thresholds, sections |
| `prototype/data/guidance.json` | Short notes on sections and circulars |
| `prototype/data/vendors.json`, `ledger_ytd.json` | Synthetic vendors and year-to-date payments |
| `prototype/tests/cases.json` | The 26 test invoices and expected answers |
| `prototype/results/` | Saved results and raw model replies |
