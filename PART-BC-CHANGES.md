# Part B and C changes (built on Part A's package)

No paid API call was made. The live adapter is covered only by mocked-transport tests. Scripted demo output is not a research result. `PRE-REGISTRATION.md`, `MONITOR-RUBRIC.md`, `pilot-settings.json`, `parallax/evidence.py` and `parallax/gate.py` are unchanged.

Tests: `python -m unittest discover -s tests` (54: A's 18 plus 36 in `tests/test_bc.py`). Six deliberate bugs (swapped direction, net-rule off by one, absolute d_z, masker numbering, one retry too few, abstention counted as a match) each made the suite fail.

## How A's modules connect
`run.py` reconciles receipts, renders views, checks invariants, collects reviews. `evaluate.evaluate_case` aggregates three reviews per view, calls `evidence.support` on every valid response, then `gate.gate` on the view aggregates, the reconciliation report and those support checks. The gate result is saved as a separate human-review decision and never removes a case from the metrics.

## B: `run.py`, `parallax/schema.py`, `parallax/monitor.py`
- Typed case validation per DATA-CONTRACT (sources, coverage, types, nonempty fields). `validate_dataset(pilot=True)` enforces exactly 20 cases, 10 harmful and 10 benign, no fault conditions.
- `--pilot`: 20 cases, 3 views, 3 repeats, no `--ledger`, `--stress`, `--limit`. Checks `pilot-settings.json` against what the code does and stops on any mismatch.
- A real pilot also needs `--cases`, a dataset manifest whose labels are REVIEWED by someone other than the author, `--max-spend-usd`, `--confirm-paid-run`, and writes to a fresh cache inside the output folder.
- Any real call needs `--confirm-paid-run`. `--max-calls` is a hard cap. A finished real run directory is not overwritten.
- Invariant failure writes an exclusion record (`exclusions.json`) and the run continues; excluded cases are never sent to the reviewer.
- Manifest adds git commit, code digest, settings and dataset hashes, spending limit, decision settings, retry policy, Python version, time. `completion.json` is written after the run.
- Adapter: 429/5xx and connection errors retried at most twice; 4xx not retried and the error body is kept; unreadable response body is a transport failure; cache writes are atomic; model settings are part of cache identity; every abstention records its cause (`INVALID_OUTPUT`, `TRANSPORT_FAILURE`, `INSUFFICIENT_EVIDENCE`). Malformed output is still never repaired.

## C: `parallax/evaluate.py`, `parallax/views.py`, cases
- Per-case: expected verdict, each view's verdict, mean, repeat SD, match with expected (null if incomplete), direction (`MORE_FORGIVING`, `STRICTER`, `UNCHANGED`, `NOT_COMPARABLE`), changed, abstention causes. All in `results.json`; main fields in `metrics.csv`.
- Summary: both directions as counts and rates for harmful and, separately, benign cases; any-flip rate; median and individual drops; d_z with an explicit undefined reason; which continuation rule fired; planned/excluded/eligible per class; abstention causes out of scheduled calls; escalation by class; accepted FLAG/NO_FLAG and mistakes among accepted; repeat variability per view. The 10-point rule uses exact fractions.
- Masker bugs fixed: numbering followed the last appearance of each actor (leaked event count and order) and substring replacement turned "Bobby" into "Actor 2by". Now first-appearance numbering and whole-word, case-insensitive, single-pass replacement. Invariants also require the relabeling to be one-to-one. This changes masked view hashes.
- `masking_residue(case)` audit lists actor names still visible after masking (in policy or event fields, or only a partial name). It warns; it does not exclude.
- `cases/pilot-candidates-DRAFT.json`: 20 varied drafts (10 scenarios, 10 actors, 1 to 2 events, scope/amount/path variants). `cases/dataset-manifest-DRAFT.json` marks every label UNREVIEWED_DRAFT. A real pilot refuses them until a second person reviews. Regenerate with `python tools_draft_pilot_cases.py`.

## Choices for A to confirm (not made silently into the protocol)
1. Any invariant failure, including the masked view, excludes the whole case. The preregistration says primary eligibility does not depend on the masked view, but the gate would otherwise accept on two views. Per-view handling needs a gate rule from A.
2. "Second teammate checks labels" is enforced as reviewer different from author in the dataset manifest.
3. `--max-spend-usd` is recorded, not enforced (no pricing is built in).
4. `pilot-settings.json` still says `consumed_by_runner: false`; the guard reads it but nothing edits it.

## Still open before a real pilot
- Model ID and spend limit; six-call live smoke test and inspection of raw outputs (not run): `python run.py --mode anthropic --model <ID> --limit 2 --repeats 1 --max-calls 6 --confirm-paid-run --out output/smoke-1`
- Second-person review of all 20 labels, manual transformation audit (at least five cases), populated dataset manifest.
- A: semantic support audit, freeze (commit, timestamp, null settings). Git repository is not initialized; `git_commit` is null until it is.
- D: fault-case tests and `report.py` does not yet display the new fields (directions, exclusions).
- The scripted reviewer keys on the phrase "Do not email", so it cannot separate the new draft cases; do not demo them as if it could.
- Cluster bootstrap and sign-flip tests remain deferred, as in the preregistration.
