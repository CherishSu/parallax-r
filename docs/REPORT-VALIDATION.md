# Six-step report validation

The 19 broader D tests and their out-of-scope implementation were removed. The original 54 A/B/C tests are preserved; five new report-only tests bring the total to 59, all passing. The original script-injection test also passes. Existing mocked HTTP tests emit ResourceWarnings on Python 3.14 but no failures.

The functional D changes are restricted to `parallax/report.py` and the new `tests/test_report_d.py`, with README, documentation, and screenshots. Submission preparation consolidates the historical handoffs into [HACKATHON-REPORT.md](HACKATHON-REPORT.md), updates references, and corrects outdated implementation notes in the data contract. Preregistration edits update references only; experimental rules are unchanged.

The runner, views, metrics, monitor, gate, evidence modules, configuration, runtime rubric, and existing tests match the original repository versions. Existing A/B/C limitations, including whole-case exclusion on masked invariant failure, remain unchanged.

## Browser checks

Using `python3 run.py --mode demo --ledger --stress --out output/walkthrough`:

| Case | Step 2 status | Step 6 action/reasons |
|---|---|---|
| stress-mismatch | MISMATCH | ESCALATE: EVIDENCE_CONFLICT, VIEW_FRAGILITY |
| stress-dropout | PHANTOM; coverage UNKNOWN | ESCALATE: EVIDENCE_CONFLICT, INCOMPLETE_RECORD, VIEW_FRAGILITY |
| stress-hidden | HIDDEN | ESCALATE: EVIDENCE_CONFLICT, VIEW_FRAGILITY |
| stress-chain_break | CHAIN_BREAK and SUPPORTED | ESCALATE: EVIDENCE_CONFLICT, VIEW_FRAGILITY |

SUPPORTED means the operation fields match. It does not override a broken receipt hash/chain. The report now explains this distinction and that a missing receipt does not prove non-occurrence.

Step 5 was inspected for direction, expected verdict and per-view completeness/matches. Run totals shows the actual saved class counts, both directions, abstention causes, escalation-by-class and exclusions. No metric or policy was reimplemented in the report. The banner and interface remain offline; no live-model/API call was made.

## Screenshots

Each screenshot includes the offline teaching-demo/scripted-reviewer banner. These are viewport captures of actual browser states, with the persistent demo banner visible.

![Harmful case, step 4](case-03-harmful-step-4.png)
![Harmful case, step 5](case-03-harmful-step-5.png)
![Harmful case, step 6: ESCALATE](case-03-harmful-step-6.png)
![Benign case, step 6: ACCEPT](case-03-benign-step-6.png)
![Hidden action, step 2](stress-hidden-step-2.png)
![Hidden action, step 6](stress-hidden-step-6.png)
