# How to use this package

Run PowerShell in the team-parallax-r folder. Claude Sonnet 5.5 is provisional. No paid calls have been made by this preparation.

## Safe commands you can run now

```powershell
python preflight.py
python -m unittest discover -s tests -q
python run.py --mode demo --limit 2 --out output/local-teaching-check
python analyze.py output/local-teaching-check/results.json --out output/local-teaching-check/statistics.json
```

preflight checks configuration, labels, current audit hashes and prompt consistency without accessing credentials. The demo uses older teaching fixtures and scripted replies; it is not evidence about real Claude behavior. analyze reads the saved results and makes no API calls. Choose a new statistics output filename if repeating analysis.

## B: after budget/account approval

Keep the API key in the local environment, never in Git or chat. Obtain approval for the actual spending limit first. The proposed $15 has NOT been authorized. max-spend-usd currently records a limit; it is NOT a dollar stop. Set an appropriate provider/account spending control and monitor usage. max-calls bounds scheduled requests, but each may have up to two transport retries. Cost estimates assume 2,000 input tokens; check actual usage during the smoke test.

Use separate teaching fixtures for the six-call connection check so intended pilot outcomes are not previewed:

```powershell
python run.py --mode anthropic --model claude-sonnet-5-5 --limit 2 --repeats 1 --max-calls 6 --confirm-paid-run --out output/smoke-1
```

Inspect all six raw answers for valid JSON, required claims, citations, truncation and returned model/usage. Do not choose the model by which gives the desired experimental effect. Fix wiring issues before freezing. Then agree the complete protocol, record the authorized budget in pilot-settings.json, and commit/freeze dataset, prompt, settings and methods before the pilot. Record that revision and UTC timestamp in PRE-REGISTRATION.md.

After those steps, replace APPROVED_AMOUNT below with the actual approved dollar amount:

```powershell
python run.py --mode anthropic --model claude-sonnet-5-5 --pilot --cases cases/pilot-candidates-DRAFT.json --dataset-manifest cases/dataset-manifest-DRAFT.json --max-calls 180 --max-spend-usd APPROVED_AMOUNT --confirm-paid-run --out output/pilot-1
python analyze.py output/pilot-1/results.json --out output/pilot-1/statistics.json
```

Never overwrite a previous real run. Cache replay is not new data. Review the output's exclusion/abstention counts before interpreting statistics. Complete PAPER-DRAFT.md from actual saved results.

## Human semantic-support inspection

For each decisive reviewer claim being inspected, read its cited record. Record whether the record actually supports that claim, not merely whether its ID exists. Save the case/view/repeat/claim ID, cited text, support decision and reason. Use supported, unsupported or unclear; preserve the original response. This is a later inspection of real judgments, not something that can be honestly completed before they exist.
