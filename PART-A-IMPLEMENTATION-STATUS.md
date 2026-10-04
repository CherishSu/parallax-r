# Part A status — October 4, 2026

## Completed locally

- Human decisions saved for all 20 candidate labels, including authorized fictional evidence amendments.
- Five human reviews of displayed cross-view summaries saved, covering allowed and prohibited examples. These were summaries, not inspection of every raw JSON field.
- Assistant preservation checks saved for all 20 cases, tied to content hashes.
- Six main reviewer instructions reviewed; runtime prompt matches REVIEWER-PROMPT.txt. Validator fields, allowed values, critical claims and null insufficient-evidence scores checked against that prompt. Remaining auxiliary fields were technically inspected, not separately approved by the user.
- Secondary-view validation failures now preserve valid primary comparisons while skipping invalid views and escalating the case.
- Scenario-cluster bootstrap and paired sign-flip analysis implemented in parallax/stats.py, available through analyze.py. Methods and limitations recorded in METRICS-AND-HANDOFF.md.
- 61 local tests pass, including a deliberately corrupted masked view, existing primary-failure tests, analytical sign-flip examples and prompt consistency.

## Remaining before a research run

- Team acceptance of assembled protocol, auxiliary fields, and exploratory analysis defaults; resolve deferred lambda/mu/delta/tau_c scope.
- Model, access, sampling settings, budget and live smoke test coordinated with B. Spending limit is recorded, not automatically enforced as dollars.
- Semantic support inspection: evidence.py verifies references exist; it does not prove that referenced text supports a conclusion.
- Commit/push reviewed changes and record the frozen dataset/prompt/settings revision and timestamp before viewing intended outcomes. Dataset remains unfrozen.
- Run the real experiment, inspect exclusions and results, then write methods/results/limitations for the paper. No real model calls were made for this implementation.

Earlier handoff documents describe older states (unreviewed labels or unimplemented statistics); use this dated update for current progress. No claim of independent real-world receipt verification is made: these receipts and events are synthetic.


## Additional local preparation

Claude Sonnet 5.5 is provisionally recorded in pilot-settings.json per the user's instruction. The output cap is 1,500; provider-default sampling is explicit. Pilot execution rejects a model/output-limit mismatch. Invalid budget values (NaN, infinity, zero and negative values) are rejected; dollar spending is still not automatically enforced.

preflight.py provides an offline readiness check and a transparent cost estimate. RUN-WHEN-READY.md contains exact local and future paid-run commands. PAPER-DRAFT.md contains methods and limitations, with no invented results. 63 tests pass. Credentials, budget authorization, live smoke test, final freeze and actual findings remain pending. This preparation does not authorize a paid call.
