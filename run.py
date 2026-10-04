"""One command runs the complete prototype and writes an offline walkthrough."""
import argparse
import csv
import datetime
import hashlib
import json
import math
import os
import subprocess
import sys
from pathlib import Path
from parallax.schema import digest, validate_dataset
from parallax.fixtures import make_cases, stress_cases
from parallax.receipts import reconcile
from parallax.views import render, check_invariants, masking_residue
from parallax.monitor import judge, prompt, MODEL_SETTINGS, MAX_RETRIES, ADAPTER_VERSION
from parallax.evaluate import evaluate_case, summary, DECISION_SETTINGS
from parallax.report import build_report

ROOT = Path(__file__).resolve().parent
PILOT_VIEWS = ['full', 'action_only', 'masked']
CSV_FIELDS = ['case_id', 'scenario_id', 'label', 'condition', 'expected_verdict', 'full_verdict', 'action_only_verdict',
              'masked_verdict', 'full_matches_expected', 'action_only_matches_expected', 'masked_matches_expected',
              'direction', 'eligible', 'delta', 'D', 'F', 'U', 'action', 'reasons']


def implemented_settings(repeats):
    """What the code actually does, in the vocabulary of pilot-settings.json."""
    return dict(cases_total=20, prohibited_cases=10, allowed_cases=10, views=PILOT_VIEWS, repeats_per_view=repeats,
                **DECISION_SETTINGS)


def settings_mismatches(path, repeats):
    """Keys where pilot-settings.json disagrees with the implemented behavior (drift guard)."""
    saved = json.loads(Path(path).read_text(encoding='utf-8-sig'))
    return [f'{k}: file has {saved.get(k)!r}, code does {v!r}' for k, v in implemented_settings(repeats).items()
            if saved.get(k) != v]


def code_digest():
    files = sorted((ROOT / 'parallax').glob('*.py')) + [ROOT / 'run.py', ROOT / 'MONITOR-RUBRIC.md']
    return digest({f.name: hashlib.sha256(f.read_bytes()).hexdigest() for f in files})


def git_commit():
    try:
        out = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=ROOT, capture_output=True, text=True, timeout=5)
        return out.stdout.strip() if out.returncode == 0 and out.stdout.strip() else None
    except (OSError, subprocess.SubprocessError):
        return None


def dataset_manifest_problems(manifest, cases):
    """A real pilot needs every case's label independently reviewed and recorded."""
    entries = {e.get('case_id'): e for e in manifest.get('cases', [])}
    problems = [f'{c["case_id"]}: missing from dataset manifest' for c in cases if c['case_id'] not in entries]
    for c in cases:
        e = entries.get(c['case_id'])
        if e and (e.get('status') != 'REVIEWED' or not e.get('label_reviewer') or not e.get('review_date')):
            problems.append(f'{c["case_id"]}: label not marked REVIEWED with reviewer and date')
        elif e and e.get('label_reviewer') in (None, '', e.get('label_author')):
            problems.append(f'{c["case_id"]}: reviewer must differ from the label author')
    return problems


def build_parser():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--mode', choices=['demo', 'anthropic'], default='demo')
    p.add_argument('--model', help='Exact model ID for a real Anthropic run')
    p.add_argument('--cases', type=Path, help='JSON array of labeled canonical cases')
    p.add_argument('--dataset-manifest', type=Path, help='JSON file with per-case provenance and label review')
    p.add_argument('--limit', type=int, default=20)
    p.add_argument('--repeats', type=int, choices=[1, 3], default=3)
    p.add_argument('--ledger', action='store_true', help='Add fourth view (changes run count)')
    p.add_argument('--stress', action='store_true', help='Add four receipt fault cases, outside primary metrics')
    p.add_argument('--replay', action='store_true', help='Require cached responses; never call API')
    p.add_argument('--pilot', action='store_true', help='Enforce the approved pilot design (20 cases, 3 views, 3 repeats)')
    p.add_argument('--settings', type=Path, default=ROOT / 'pilot-settings.json', help='Settings file checked against the code in pilot mode')
    p.add_argument('--max-spend-usd', type=float, help='Spending limit, recorded in the manifest (required for a real pilot)')
    p.add_argument('--max-calls', type=int, help='Refuse to start if more calls than this would be scheduled')
    p.add_argument('--confirm-paid-run', action='store_true', help='Required before any real API call is made')
    p.add_argument('--cache-dir', type=Path, help='Response cache; a real pilot defaults to a fresh one inside --out')
    p.add_argument('--allow-overwrite', action='store_true', help='Allow writing into a directory that holds an earlier real run')
    p.add_argument('--out', type=Path)
    return p


def main(argv=None):
    p = build_parser()
    args = p.parse_args(argv)
    real = args.mode == 'anthropic'
    if args.max_spend_usd is not None and (not math.isfinite(args.max_spend_usd) or args.max_spend_usd <= 0):
        p.error('--max-spend-usd must be a finite positive amount')
    if args.limit < 1:
        p.error('--limit must be positive')
    if real and not args.model:
        p.error('--model is required for a real run')
    if real and not args.replay:
        if not args.confirm_paid_run:
            p.error('Real API calls cost money. Re-run with --confirm-paid-run when you intend that; no calls made.')
        if not os.environ.get('ANTHROPIC_API_KEY'):
            p.error('ANTHROPIC_API_KEY is not set; no network calls made')
    if args.pilot:
        if args.repeats != 3 or args.ledger or args.stress or args.limit != 20:
            p.error('--pilot means exactly 20 cases, 3 views, 3 repeats: no --ledger, --stress, --limit or --repeats 1')
        if real and not args.cases:
            p.error('A real pilot needs --cases with the reviewed dataset, not the bundled teaching fixtures')
        if real and not args.dataset_manifest:
            p.error('A real pilot needs --dataset-manifest recording provenance and label review')
        if real and not args.replay and args.max_spend_usd is None:
            p.error('A real pilot needs --max-spend-usd so the limit is written to the manifest')
        if real and args.replay and not args.cache_dir:
            p.error('Replaying a real pilot needs --cache-dir pointing at the original run cache')
        if not args.settings.exists():
            p.error(f'Settings file not found: {args.settings}')
        drift = settings_mismatches(args.settings, args.repeats)
        if drift:
            p.error('pilot-settings.json disagrees with the code; fix one before running:\n  ' + '\n  '.join(drift))
    model = 'scripted-teaching-reviewer-v1' if not real else args.model
    cases = json.loads(args.cases.read_text(encoding='utf-8-sig')) if args.cases else make_cases()
    if not isinstance(cases, list) or not cases:
        p.error('Cases file must be a nonempty JSON array')
    cases = cases[:args.limit]
    if args.stress:
        if args.cases:
            p.error('--stress is only supported with the bundled teaching cases')
        cases += stress_cases(cases[0])
    try:
        counts = validate_dataset(cases, pilot=args.pilot)
    except ValueError as exc:
        p.error(str(exc))
    dataset_manifest = None
    if args.dataset_manifest:
        dataset_manifest = json.loads(args.dataset_manifest.read_text(encoding='utf-8-sig'))
        problems = dataset_manifest_problems(dataset_manifest, cases)
        if problems and args.pilot and real:
            p.error('Dataset manifest is not ready for a real pilot:\n  ' + '\n  '.join(problems[:12]))
    if args.pilot and real:
        configured = json.loads(args.settings.read_text(encoding='utf-8-sig'))
        if configured.get('model_id') != args.model or configured.get('max_output_tokens') != MODEL_SETTINGS['max_tokens']:
            p.error('Pilot model or output-token limit differs from the recorded settings')
    names = PILOT_VIEWS + (['ledger'] if args.ledger else [])
    scheduled = len(cases) * len(names) * args.repeats
    if args.max_calls is not None and scheduled > args.max_calls:
        p.error(f'{scheduled} calls would be scheduled, above --max-calls {args.max_calls}')
    out = (args.out or ROOT / 'output' / args.mode).resolve()
    if real and not args.allow_overwrite and any((out / f).exists() for f in ('manifest.json', 'results.json')):
        p.error(f'{out} already holds a real run. Choose a fresh --out directory (or pass --allow-overwrite).')
    cache_dir = (args.cache_dir or (out / 'cache' if args.pilot and real else ROOT / 'cache' / args.mode)).resolve()
    out.mkdir(parents=True, exist_ok=True)
    manifest = dict(mode=args.mode, model=model, repeats=args.repeats, views=names,
                    case_hash=digest(cases), prompt_hash=digest(prompt()), threshold=.5,
                    model_settings=MODEL_SETTINGS, case_ids=[c['case_id'] for c in cases], scheduled_calls=scheduled,
                    pilot_mode=args.pilot, dataset_counts=counts, adapter_version=ADAPTER_VERSION,
                    retry_policy={'max_retries': MAX_RETRIES, 'retry_on': 'connection errors and HTTP 429/5xx only'},
                    decision_settings=implemented_settings(args.repeats),
                    settings_file_hash=digest(json.loads(args.settings.read_text(encoding='utf-8-sig'))) if args.settings.exists() else None,
                    dataset_manifest_hash=digest(dataset_manifest) if dataset_manifest else None,
                    max_spend_usd=args.max_spend_usd, code_digest=code_digest(), git_commit=git_commit(),
                    python_version=sys.version.split()[0], cache_dir=str(cache_dir), replay=args.replay,
                    created_at=datetime.datetime.now(datetime.timezone.utc).isoformat())
    (out / 'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    (out / 'cases.json').write_text(json.dumps(cases, indent=2), encoding='utf-8')
    (out / 'prompt.txt').write_text(prompt(), encoding='utf-8')
    print(f"{args.mode.upper()}: {len(cases)} cases x {len(names)} views x {args.repeats} repeats = {scheduled} reviews"
          + ('' if args.pilot else '  (not a pilot run)'), flush=True)
    results, exclusions, residues = [], [], {}
    for case in cases:
        report = reconcile(case)
        views = [render(case, report, n) for n in names]
        try:
            check_invariants(case, report, [v for v in views if v['name'] in ('full', 'action_only')])
        except ValueError as exc:
            # Preserve the evidence of what happened and keep going; excluded cases are never sent to the reviewer.
            exclusions.append(dict(case_id=case['case_id'], scenario_id=case['scenario_id'], ground_truth=case['ground_truth'],
                                   condition=case.get('condition'), stage='invariant_check', reason=str(exc)))
            print(f"  {case['case_id']}: EXCLUDED before review ({exc})", flush=True)
            continue
        found = masking_residue(case)
        if found:
            residues[case['case_id']] = found
        view_failures = {}
        for v in views:
            if v['name'] in ('full', 'action_only'):
                continue
            try:
                check_invariants(case, report, [v])
            except ValueError as exc:
                view_failures[v['name']] = str(exc)
        rows = []
        for v in views:
            for repeat in range(1, args.repeats + 1):
                if v['name'] in view_failures:
                    rows.append(dict(view=v['name'], repeat=repeat, judgment=None, verdict='ABSTAIN',
                                     cache_hit=False, error='view_validation_failure',
                                     abstain_cause='VIEW_VALIDATION_FAILURE',
                                     skipped=True, reason=view_failures[v['name']]))
                else:
                    rows.append(judge(v, case['case_id'], repeat, args.mode, model, cache_dir, args.replay))
        metrics = evaluate_case(case, report, views, rows, args.repeats)
        metrics['view_validation_failures'] = view_failures
        if view_failures:
            metrics['decision']['action'] = 'ESCALATE'
            metrics['decision']['accepted_verdict'] = None
            metrics['decision']['reason_codes'].append('VIEW_VALIDATION_FAILURE')
            metrics['decision']['details']['view_validation_failures'] = view_failures
        results.append(dict(case=case, reconciliation=report, views=views, rows=rows, metrics=metrics))
        print(f"  {case['case_id']}: {metrics['decision']['action']} {' '.join(metrics['decision']['reason_codes'])}", flush=True)
    run = dict(mode=args.mode, manifest=manifest, summary=summary(results, args.mode, exclusions), results=results,
               exclusions=exclusions, masking_residue=residues)
    (out / 'results.json').write_text(json.dumps(run, indent=2), encoding='utf-8')
    (out / 'exclusions.json').write_text(json.dumps(exclusions, indent=2), encoding='utf-8')
    (out / 'report.html').write_text(build_report(run), encoding='utf-8')
    with (out / 'metrics.csv').open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        writer.writeheader()
        for r in results:
            m, vr = r['metrics'], r['metrics']['view_results']
            row = dict(case_id=r['case']['case_id'], scenario_id=r['case']['scenario_id'], label=r['case']['ground_truth'],
                       condition=r['case'].get('condition', 'clean'), expected_verdict=m['expected_verdict'],
                       direction=m['direction'], eligible=m['eligible'], action=m['decision']['action'],
                       reasons=';'.join(m['decision']['reason_codes']), **{k: m[k] for k in ('delta', 'D', 'F', 'U')})
            for view in PILOT_VIEWS:
                row[f'{view}_verdict'] = vr[view]['verdict']
                row[f'{view}_matches_expected'] = vr[view]['matches_expected']
            writer.writerow(row)
    (out / 'completion.json').write_text(json.dumps(dict(
        completed_at=datetime.datetime.now(datetime.timezone.utc).isoformat(), cases_judged=len(results),
        cases_excluded=len(exclusions), excluded=exclusions, cache_hits=run['summary']['cache_hits'],
        masking_residue_cases=sorted(residues), note='Cached responses are replay, not new independent draws.'), indent=2), encoding='utf-8')
    s = run['summary']
    print(f"Planned {len(cases)} cases: {len(results)} judged, {len(exclusions)} excluded before review. Pilot status: {s['pilot_status']}.")
    if residues:
        print(f"  Identity-masking audit flagged {len(residues)} case(s): see results.json masking_residue (does not block the primary comparison).")
    print(f"Open {out / 'report.html'}")
    print('DEMO ONLY: scripted outputs are not research evidence.' if args.mode == 'demo' else 'Exploratory real-model run. Inspect errors and exclusions before interpreting results.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
