"""Offline readiness check. Does not read credentials or call an API."""
import json
from pathlib import Path
from parallax.schema import digest, validate_dataset
from parallax.views import render, check_invariants
from parallax.receipts import reconcile
from parallax.monitor import prompt, MODEL_SETTINGS
from run import settings_mismatches, dataset_manifest_problems

ROOT = Path(__file__).resolve().parent


def check():
    settings = json.loads((ROOT / 'pilot-settings.json').read_text(encoding='utf-8-sig'))
    cases = json.loads((ROOT / 'cases/pilot-candidates-DRAFT.json').read_text(encoding='utf-8'))
    manifest = json.loads((ROOT / settings['case_manifest']).read_text(encoding='utf-8'))
    problems = settings_mismatches(ROOT / 'pilot-settings.json', 3)
    problems += dataset_manifest_problems(manifest, cases)
    counts = validate_dataset(cases, pilot=True)
    if prompt().strip() != (ROOT / 'REVIEWER-PROMPT.txt').read_text(encoding='utf-8').strip():
        problems.append('Reviewed prompt differs from runtime prompt')
    if settings['max_output_tokens'] != MODEL_SETTINGS['max_tokens']:
        problems.append('Output token limit differs from runtime')
    notes = {n['case_id']: n for n in manifest['cases']}
    audited_labels = []
    lengths = []
    for c in cases:
        views = [render(c, reconcile(c), n) for n in ('full', 'action_only', 'masked')]
        check_invariants(c, reconcile(c), views)
        lengths.extend(len(prompt()) + len(json.dumps(v['payload'])) for v in views)
        audit = notes[c['case_id']].get('assistant_transformation_check') or {}
        if audit.get('case_digest') != digest(c):
            problems.append(c['case_id'] + ': assistant audit stale or missing')
        human = notes[c['case_id']].get('transformation_audit') or {}
        if human.get('result') == 'PASS' and human.get('case_digest') == digest(c):
            audited_labels.append(c['ground_truth'])
    if len(audited_labels) < 5 or set(audited_labels) != {'harmful', 'benign'}:
        problems.append('Need five current human comparison checks covering both classes')
    return dict(local_checks='PASS' if not problems else 'FAIL', problems=problems,
                counts=counts, human_comparison_checks=len(audited_labels),
                model=settings['model_id'], frozen=False,
                input_characters=dict(min=min(lengths), max=max(lengths)),
                pending=['Team acceptance of assembled protocol and analysis defaults',
                         'Budget authorization and account access',
                         'Live smoke test on separate teaching fixtures',
                         'Git revision and protocol freeze before pilot outcomes'],
                cost_estimate=dict(currency='USD', scheduled_answers=180,
                    assumed_input_tokens_per_call=2000, output_tokens_per_call=[500,1500],
                    estimated_pilot_range=[1.62,3.42],
                    estimated_six_call_smoke_max=.114,
                    estimated_pilot_plus_smoke_three_attempts=10.602,
                    proposed_budget=15, authorized_budget=settings['max_spend_usd'],
                    caveat='Planning estimates, not exact token counts or enforced billing limits. Rates: input $2/M, output $10/M; no tax or discounts.'))


if __name__ == '__main__':
    result = check()
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result['local_checks'] == 'PASS' else 1)
