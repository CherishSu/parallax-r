# Team handoff and implementation boundaries

## Current status

The local end-to-end prototype is implemented. Demo data, receipt checks, four views, invariants, structured reviewer validation, a scripted reviewer, a real Anthropic adapter, repeat-aware caching, metrics, a decision gate, offline HTML, JSON/CSV artifacts, and automated tests are present.

Live paid API calls have not been performed. Unit tests exercise the real adapter's response parsing with mocked API responses. The HTML is a saved report, not an upload server or live dashboard. Use `--cases` for custom input.

The implementation is a teaching prototype aligned with the initial pilot. It is not the full research blueprint: no deployment-grade independent receipt sink, coverage estimator, semantic claim verifier, multiple monitor families, calibrated 1% FPR, bootstrap/permutation inference, full baseline/ablation grid, real swarm dataset integration, or research paper is supplied.

## Ownership and execution order

| Owner | Files to work on | First task | Done when |
|---|---|---|---|
| A | `PRE-REGISTRATION.md`, `MONITOR-RUBRIC.md`, `parallax/gate.py`, `parallax/evidence.py` | Review labels, preserve permission/context, agree on decision rules | The team can explain one case and accepts the frozen rules |
| B | `run.py`, `parallax/schema.py`, `parallax/monitor.py`, `parallax/receipts.py` | Run six real API calls, inspect raw answers and schema errors | The real report works and cached replay needs no network |
| C | `parallax/fixtures.py`, `parallax/views.py`, metrics in `parallax/evaluate.py` | Replace filename variants with diverse reviewed cases; audit transformations | Cases have defensible labels and comparisons preserve evidence |
| D | Invariant checks in `parallax/views.py`, fault cases, `parallax/report.py`, tests | Test changed permissions, hidden actions, broken receipts; improve demo | Each failure is detected and explained on screen |

A's evidence and decision functions now live in `parallax/evidence.py` and `parallax/gate.py`; C's metrics remain in `parallax/evaluate.py`. See PART-A-CODE.md for integration. Renderers and invariant checks still share `views.py`; assign a file owner or split that module before parallel editing.

## Run commands

```powershell
# Full teaching walkthrough: 24 cases, 4 views, 3 repeats = 288 scripted reviews
python run.py --mode demo --ledger --stress

# Initial pilot shape: 20 cases, 3 views, 3 repeats = 180 scripted reviews
python run.py --mode demo --out output/pilot-shape

# Replay the teaching walkthrough without generating missing responses
python run.py --mode demo --ledger --stress --replay --out output/replay

# Automated checks
python -m unittest discover -s tests -v
```

The four stress cases are excluded from primary harmful/benign pilot metrics but included in overall run and escalation totals. D/F always use the first three views. The gate uses all selected views, including ledger when enabled. The ledger is deliberately a simple alternate JSON presentation in v1.

## Data and trust boundaries

- `case_id` identifies one item; `scenario_id` links related variants.
- `ground_truth` is for human evaluation and never sent to the reviewer.
- The `narrative` field may contain removable explanation only. Facts affecting permission, outcomes, or context belong in canonical evidence. Automated checks cannot enforce this semantic distinction.
- The task, policy, canonical events, receipts, and reconciliation report are shown in every view. This prototype does not implement a separate raw/no-receipts baseline.
- Receipt hashes detect modifications relative to their current links, not a powerful attacker rewriting the entire log. Production needs an independently anchored sink.
- Only `KNOWN_COMPLETE_SYNTHETIC` allows the completeness check to pass in this prototype. Real records with unknown completeness escalate. Do not label real records synthetically complete to bypass this limitation.
- All unmatched/hidden/mismatched actions are conservatively treated as important for the demo gate. A must specify a real criticality policy for deployment.
- U detects unresolved citations, not whether a cited record logically proves the claim. Manual auditing is still required.
- Masking replaces known actor display labels. It is not a general anonymizer and does not scrub arbitrary identity references from imported narratives.

## Reviewer calls and reproducibility

The real adapter uses Anthropic's Messages endpoint and passes the instruction from `MONITOR-RUBRIC.md` plus the required output field definitions. It does not send the illustrative answer in that document. Model settings use a maximum of 1500 output tokens and provider-default sampling; the manifest records this. Select and record an exact available model ID.

References: [Messages API](https://platform.claude.com/docs/en/api/messages/create) and [API overview](https://platform.claude.com/docs/en/api/overview).

Cache identity includes model, mode, case, view name/hash, repeat ID, prompt hash, and adapter version. Each repeat is a distinct scheduled request; replay reuses it. Raw responses include provider usage when returned. Actual monetary cost is not calculated because pricing depends on the selected model; use provider usage/billing records.

Malformed successful outputs become ABSTAIN without repair prompts. Transport/rate-limit/server errors get at most two retries, with attempt statuses recorded. Nonretryable HTTP errors are recorded as failed calls. Errors never become harmless judgments.

Generated artifacts and caches are ignored by Git by default because future runs may contain sensitive data. Before sharing an offline demo, explicitly review and package a safe fictional report or cache. Keys are not written to cache files. There is no Git repository initialized here by this prototype.

## Before calling the run research

1. Replace repetitive teaching fixtures with independently reviewed cases and record provenance.
2. Fix and review the canonical schema and all context-preserving transformations.
3. Choose actual model settings and a separate calibration design if claiming a false-positive operating point.
4. Freeze the preregistration, cases, prompts, and thresholds before examining the intended test outcomes.
5. Run real reviews, audit failures and exclusions, and report denominator counts.
6. Treat bootstrap estimates at the scenario level when variants are related; do not treat repeated calls as independent cases.
7. Report observed results, including no effect. The scripted flip in the teaching demo is never a research result.

The CLI saves a run manifest before calls, but this is not a replacement for a reviewed, committed preregistration. The earlier documents remain draft until the team completes that step.
