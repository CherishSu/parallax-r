# Parallax-R working teaching prototype

Start with [START-HERE.md](START-HERE.md). It explains the project without requiring you to understand the research blueprint.

```powershell
python run.py --mode demo --ledger --stress
```

Open `output/demo/report.html` in a browser. Select a case and click the six numbered steps.

Python 3.10 or newer is sufficient. There are no packages to install, no API key needed for the demo, and no network calls in demo mode. Tested locally with Python 3.13 on Windows.

The demo's reviewer is **scripted**, its cases are **fictional**, and its receipts are **synthetic**. The disagreement is programmed to explain the system. It is not a measured finding about an AI model.

The real Anthropic adapter, cached replay, structured validation, receipt reconciliation, view invariants, per-case metrics, decision gate, CSV/JSON exports, and offline report are implemented. Live API execution requires your own credentials and model selection; it has not been verified against a paid live endpoint in this workspace.

See [TEAM-HANDOFF.md](TEAM-HANDOFF.md) for component ownership, limitations, and a real-run checklist. The earlier preregistration documents remain drafts; this teaching run does not freeze or complete the research experiment.

```powershell
python -m unittest discover -s tests -v
```
