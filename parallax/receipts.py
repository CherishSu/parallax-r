"""Synthetic receipts and cross-checking (B, with fault fixtures from D)."""
from .schema import digest


def make_receipts(events):
    receipts, previous = [], 'GENESIS'
    for e in events:
        r = dict(receipt_id='R-' + e['event_id'], event_id=e['event_id'],
                 operation=e['operation'], resource=e['resource'], output=e['output'], previous_digest=previous)
        r['receipt_digest'] = digest(r)
        previous = r['receipt_digest']
        receipts.append(r)
    return receipts


def reconcile(case):
    findings, previous = [], 'GENESIS'
    for r in case['receipts']:
        if r['previous_digest'] != previous or r['receipt_digest'] != digest({k: v for k, v in r.items() if k != 'receipt_digest'}):
            findings.append({'status': 'CHAIN_BREAK', 'event_id': r['event_id'], 'receipt_ids': [r['receipt_id']]})
        previous = r['receipt_digest']
    for e in case['events']:
        matches = [r for r in case['receipts'] if r['event_id'] == e['event_id']]
        status = 'PHANTOM' if not matches else ('SUPPORTED' if len(matches) == 1 and all(matches[0][k] == e[k] for k in ('operation', 'resource', 'output')) else 'MISMATCH')
        findings.append({'status': status, 'event_id': e['event_id'], 'receipt_ids': [r['receipt_id'] for r in matches]})
    ids = {e['event_id'] for e in case['events']}
    for r in case['receipts']:
        if r['event_id'] not in ids:
            findings.append({'status': 'HIDDEN', 'event_id': r['event_id'], 'receipt_ids': [r['receipt_id']]})
    return {'findings': findings, 'coverage': case['coverage'], 'synthetic': case.get('synthetic', False)}
