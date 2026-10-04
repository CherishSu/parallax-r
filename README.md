# Parallax-R

Parallax-R compares a reviewer's judgments across different presentations of the same recorded action, checks evidence references, and marks inconsistent cases for human review.

**Hackathon prototype:** the offline demo uses fictional cases, synthetic receipts, and a scripted reviewer. Its outcomes are programmed demonstrations, not real-model research findings.

## Run the demo

Python 3.10 or newer; no packages, API key, or internet connection required. From this folder:

```sh
python3 -m unittest discover -s tests
python3 run.py --mode demo --ledger --stress --out output/walkthrough
open output/walkthrough/report.html
```

On platforms without macOS `open`, open the HTML manually in a browser. No server is needed. Choose a case and follow the six steps: What happened → Check records → Make versions → Ask reviewer → Compare → Decide.

The walkthrough contains 24 cases × four views × three repeats = 288 scripted response records. The suite contains 59 tests.

## Project documentation

- [Hackathon report](docs/HACKATHON-REPORT.md): purpose, architecture, A/B/C/D contributions, metrics, demonstration, limitations, and future work.
- [Validation and screenshots](docs/REPORT-VALIDATION.md): report checks and fault-case outcomes.
- [Data contract](DATA-CONTRACT.md): input and output structures.
- [Metric specification](METRICS-AND-HANDOFF.md): formulas and missing-data rules.
- [Draft research plan](PRE-REGISTRATION.md): proposed pilot; not frozen or completed.
- [Runtime reviewer rubric](MONITOR-RUBRIC.md): loaded by the code; keep this file at the repository root.

## Repository map

| Path | Purpose |
|---|---|
| `run.py` | Command-line runner |
| `parallax/` | Evidence, views, reviewer, metrics, gate, and HTML report |
| `tests/` | Pipeline and report tests |
| `docs/` | Hackathon report, validation notes, and six screenshots |
| `cases/` | Unreviewed draft pilot candidates and label manifest |
| `pilot-settings.json` | Selected pilot settings checked by the runner |
| `tools_draft_pilot_cases.py` | Draft-case generator |
| `demo.ps1` | Optional PowerShell demo launcher |
| `output/walkthrough/` | Generated report and JSON/CSV results; Git-ignored |

The real-model adapter has mocked-transport coverage but has not been validated against a paid endpoint here. The report documents remaining research and implementation limitations. No real-model run is required for this demo.
