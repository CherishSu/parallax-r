# Part A evidence and decision modules

This code update adds separate `parallax/evidence.py` and `parallax/gate.py` modules and connects them to the existing runner. It does not run a real AI experiment or complete the later statistical analysis.

## What evidence.py does

Imagine the reviewer says: “The actor broke the rule; see record E1.”

1. The checker reads the reviewer's claims marked critical to its conclusion.
2. It looks up the supplied event and receipt IDs for this case.
3. It checks whether each critical claim has any references and whether all of them exist in the correct list.
4. It returns the IDs of claims with problems, the unknown references, and the fraction of critical claims with reference problems, called U.

If all references exist, that does not prove the claim is right. E1 could exist but be irrelevant. The result explicitly says `semantic_support: NOT_CHECKED`; a human must inspect whether the claim follows from the record. Never describe this module as full fact checking.

## What gate.py does

1. Receive the overall verdict for each required version from the metrics code.
2. Read the receipt reconciliation report and evidence-reference check results.
3. Look for conflicting records, unknown completeness, missing claim references, disagreement between versions, or an incomplete/missing review.
4. If any check triggers, return ESCALATE, meaning “human review needed,” with all applicable reason codes and details.
5. Otherwise return ACCEPT and the shared verdict, which can be FLAG or NO_FLAG. ACCEPT does not mean the actor was safe; it means the implemented checks did not reject that shared judgment.

Nothing is emailed or sent to a person. The result is saved for review. The gate does not remove cases from experiment measurements. Evidence-preservation checks and JSON validation must already have run upstream.

## How the modules connect

`run.py` prepares views and collects responses. `parallax/evaluate.py` combines the three reviews per version and calculates measurements. It calls `support()` in `evidence.py`, then `gate()` in `gate.py` to obtain a separate human-review decision.

Person A owns the new two modules. Person C can work on the calculations in `evaluate.py` without editing A's decision rules. Existing imports of `support` from `evaluate.py` still work for compatibility, but new code should import it directly from `parallax.evidence`.

## Interfaces for teammates

```python
from parallax.evidence import support
from parallax.gate import gate

# judgment must already pass validate_judgment().
check = support(judgment, case)

# Each group must be an aggregate containing complete and verdict.
# Pass a support check for every available validated response, including
# view/repeat metadata so diagnostic claim IDs can be located.
decision = gate(groups, reconciliation_report, support_checks, case,
                required_views=('full', 'action_only', 'masked'))
```

`support()` preserves the original `U` and `unresolved_claims` fields and adds `critical_claim_count`, `citation_issues`, and `semantic_support`. With no critical claims, U is null. An ASSESSED response with no critical claims must be rejected upstream by schema validation.

`gate()` preserves `action`, `accepted_verdict`, `reason_codes`, `event_ids`, and `receipt_ids`. It adds `details` with required/missing views, per-view verdicts, evidence conflicts, support-check failures, and coverage status. Missing required views request human review. Unknown extra views or an empty required-view list produce a caller error rather than silently ignoring data.

## Run the checks

From the extracted code directory, with Python 3.10 or newer:

```powershell
python -m unittest discover -s tests -v
python run.py --mode demo --ledger --stress --out output/part-a-check
```

Open `output/part-a-check/report.html` to inspect saved results. The expanded walkthrough has 24 cases and 288 scripted responses. For the selected pilot shape instead, run:

```powershell
python run.py --mode demo --out output/pilot-shape
```

That uses 20 cases, three views, and three reviews: 180 scripted responses. Neither command needs an API key or internet access. Scripted answers are not real AI findings.

## What this package does not complete

- Semantic claim support: a valid citation can still be irrelevant.
- Real independent receipts, their trusted anchoring, or statistical coverage estimation.
- Delta/tau_c calibration or a combined EFI with lambda/mu weights.
- Reading all selected settings from a config file; existing code still contains fixed settings.
- Bootstrap/permutation inference, a reviewed diverse dataset, or paper findings.

The other known research-pipeline gaps remain listed in DATA-CONTRACT.md. This is the initial gate/evidence implementation, not proof of their effectiveness.

## Sharing

`Part-A-Code.zip` contains the runnable prototype, tests, and current documentation. It deliberately excludes API keys, caches, generated outputs, and the original source documents. Your earlier `Part-A-Handoff.zip` remains the document-only package you already shared; this code ZIP is an additional delivery. Extract it into a new directory before comparing or merging with teammates' work, rather than overwriting their files blindly.
