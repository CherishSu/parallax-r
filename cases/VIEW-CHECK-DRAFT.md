# Draft dataset: comparison of the three versions

Checked 2026-10-04 by Codex (AI assistant). All 20 cases passed the version-preservation check. All 20 labels have separately been reviewed by the human user.

For each case, generated full, action-only and masked views from the current dataset. Compared all evidence fields, verified the explanation removal and name replacement, checked synthetic receipt consistency, and inspected whether removing the explanation removes a necessary permission fact. The manifest records case digests and view hashes so this check is tied to the current content.

The earlier additions remain present in every version: maintenance-window timing (example 4), unapproved server status (example 9), no credentials or keys in the file (example 12), and internal-account status (example 16). Excuses remain in full and masked views.

## Limits

This checks preservation of the supplied fictional evidence, not whether it describes real events. Receipts were generated from the fictional events, so matching hashes are not independent proof. The private-key example relies on the supplied path and the personnel example on the recorded message; actual file or attachment contents were not inspected. No new cross-view discrepancy was found in these cases.

This is an assistant audit, not a human transformation audit. Existing human transformation_audit fields remain unchanged. The dataset is still a draft and is not frozen. No real AI reviewer calls were made, and this report does not show whether excuses influence reviewers.

## Per-case results

| Case | Version-preservation check |
| --- | --- |
| cand-01-harmful | PASS |
| cand-01-benign | PASS |
| cand-02-harmful | PASS |
| cand-02-benign | PASS |
| cand-03-harmful | PASS |
| cand-03-benign | PASS |
| cand-04-harmful | PASS |
| cand-04-benign | PASS |
| cand-05-harmful | PASS |
| cand-05-benign | PASS |
| cand-06-harmful | PASS |
| cand-06-benign | PASS |
| cand-07-harmful | PASS |
| cand-07-benign | PASS |
| cand-08-harmful | PASS |
| cand-08-benign | PASS |
| cand-09-harmful | PASS |
| cand-09-benign | PASS |
| cand-10-harmful | PASS |
| cand-10-benign | PASS |
