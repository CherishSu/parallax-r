"""Shared data rules and reproducible fingerprints (Person B)."""
import hashlib
import json
import math


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()).hexdigest()


SOURCES = ('RECEIPT_BACKED', 'ENVIRONMENT_OBSERVED', 'AGENT_CLAIMED', 'INFERRED')
COVERAGE = ('KNOWN_COMPLETE_SYNTHETIC', 'UNKNOWN')
LABELS = ('harmful', 'benign')
EVENT_FIELDS = ('event_id', 'actor', 'operation', 'resource', 'output', 'source')
RECEIPT_FIELDS = ('receipt_id', 'event_id', 'operation', 'resource', 'output', 'previous_digest', 'receipt_digest')


def _text(value, where, name):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f'{where}: {name} must be a nonempty string')
    return value


def validate_case(case):
    """Enforce the typed contract in DATA-CONTRACT.md (one case, not a dataset)."""
    if not isinstance(case, dict):
        raise ValueError('Case must be a JSON object')
    for key in ('case_id', 'scenario_id', 'task', 'policy', 'events', 'receipts', 'narrative', 'coverage'):
        if key not in case:
            raise ValueError(f'Missing case field: {key}')
    where = f"case {case['case_id']!r}"
    for key in ('case_id', 'scenario_id', 'policy'):
        _text(case[key], where, key)
    for key in ('task', 'narrative'):
        if not isinstance(case[key], str):
            raise ValueError(f'{where}: {key} must be a string')
    if case['coverage'] not in COVERAGE:
        raise ValueError(f'{where}: coverage must be one of {COVERAGE}')
    if 'synthetic' in case and type(case['synthetic']) is not bool:
        raise ValueError(f'{where}: synthetic must be true or false')
    if 'ground_truth' in case and case['ground_truth'] not in LABELS:
        raise ValueError(f'{where}: ground_truth must be one of {LABELS}')
    if 'condition' in case and (not isinstance(case['condition'], str) or not case['condition'].strip()):
        raise ValueError(f'{where}: condition, if present, must be a nonempty string')
    if not isinstance(case['events'], list) or not isinstance(case['receipts'], list):
        raise ValueError(f'{where}: events and receipts must be lists')
    for event in case['events']:
        if not isinstance(event, dict):
            raise ValueError(f'{where}: every event must be an object')
        for key in EVENT_FIELDS:
            if key not in event:
                raise ValueError(f'Missing event field: {key}')
            _text(event[key], where, f'event {key}')
        if event['source'] not in SOURCES:
            raise ValueError(f"{where}: event {event['event_id']} has unknown source {event['source']!r}")
    for receipt in case['receipts']:
        if not isinstance(receipt, dict):
            raise ValueError(f'{where}: every receipt must be an object')
        for key in RECEIPT_FIELDS:
            if key not in receipt:
                raise ValueError(f'Missing receipt field: {key}')
            _text(receipt[key], where, f'receipt {key}')
    ids = [e['event_id'] for e in case['events']]
    if len(ids) != len(set(ids)) or 'POLICY' in ids:
        raise ValueError('Duplicate or reserved event ID')
    rids = [r['receipt_id'] for r in case['receipts']]
    if len(rids) != len(set(rids)):
        raise ValueError('Duplicate receipt ID')
    return case


def validate_dataset(cases, pilot=False):
    """Validate a case list. pilot=True also enforces the approved 20-case design."""
    if not isinstance(cases, list) or not cases:
        raise ValueError('Cases must be a nonempty JSON array')
    for case in cases:
        validate_case(case)
        if case.get('ground_truth') not in LABELS:
            raise ValueError(f"case {case['case_id']!r}: every case needs a human-assigned harmful/benign ground_truth")
    ids = [c['case_id'] for c in cases]
    if len(ids) != len(set(ids)):
        raise ValueError('Case IDs must be unique')
    counts = {'total': len(cases), 'harmful': sum(c['ground_truth'] == 'harmful' for c in cases),
              'benign': sum(c['ground_truth'] == 'benign' for c in cases)}
    if pilot:
        if counts['total'] != 20 or counts['harmful'] != 10 or counts['benign'] != 10:
            raise ValueError(f"Pilot needs exactly 20 cases, 10 harmful and 10 benign; got {counts}")
        if any(c.get('condition') for c in cases):
            raise ValueError('Pilot cases may not carry fault-test conditions')
    return counts


def validate_judgment(j):
    fields = {'assessment_status', 'risk_score', 'violation_category', 'confidence', 'intent_assessment', 'rationale', 'claims'}
    if not isinstance(j, dict) or set(j) != fields:
        raise ValueError('Judgment must have exactly the rubric fields')
    if j['assessment_status'] not in ('ASSESSED', 'INSUFFICIENT_EVIDENCE'):
        raise ValueError('Unknown status')
    def probability(x):
        return type(x) in (int, float) and math.isfinite(x) and 0 <= x <= 1
    if not probability(j['confidence']):
        raise ValueError('Invalid confidence')
    if j['assessment_status'] == 'ASSESSED':
        if not probability(j['risk_score']):
            raise ValueError('Invalid risk score')
    elif j['risk_score'] is not None:
        raise ValueError('Insufficient evidence requires null risk')
    if j['violation_category'] not in ('NONE', 'UNAUTHORIZED_ACCESS', 'UNAUTHORIZED_DISCLOSURE', 'DESTRUCTIVE_ACTION', 'MISREPRESENTATION', 'OTHER', 'UNCERTAIN'):
        raise ValueError('Invalid category')
    if j['intent_assessment'] not in ('UNKNOWN', 'STATED_BENIGN', 'STATED_HARMFUL', 'MIXED'):
        raise ValueError('Invalid intent')
    if not isinstance(j['rationale'], str) or not j['rationale'].strip() or not isinstance(j['claims'], list):
        raise ValueError('Invalid rationale or claims')
    seen = set()
    for c in j['claims']:
        if not isinstance(c, dict) or set(c) != {'claim_id', 'text', 'critical', 'event_ids', 'receipt_ids'}:
            raise ValueError('Invalid claim fields')
        for key in ('claim_id', 'text'):
            if not isinstance(c[key], str) or not c[key].strip():
                raise ValueError('Empty claim text or ID')
        if c['claim_id'] in seen or type(c['critical']) is not bool:
            raise ValueError('Invalid claim ID or critical flag')
        seen.add(c['claim_id'])
        for key in ('event_ids', 'receipt_ids'):
            if not isinstance(c[key], list) or any(not isinstance(x, str) for x in c[key]):
                raise ValueError('Invalid citations')
    if j['assessment_status'] == 'ASSESSED' and not any(c['critical'] for c in j['claims']):
        raise ValueError('Assessed response needs a critical claim')
    return j
