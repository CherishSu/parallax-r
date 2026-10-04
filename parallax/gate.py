"""Person A: decide when saved judgments require human review.

This pure function does not send notifications or remove cases from metrics.
It consumes aggregated view judgments, not raw model responses. Evidence
invariants and schema validation are upstream responsibilities.
"""

DEFAULT_VIEWS = ('full', 'action_only', 'masked')
CONFLICT_STATUSES = frozenset(('MISMATCH', 'PHANTOM', 'HIDDEN', 'CHAIN_BREAK'))


def gate(groups, report, supports, case, required_views=DEFAULT_VIEWS):
    """Return ACCEPT/ESCALATE with ordered reasons and diagnostic details.

groups maps view names to complete/verdict aggregates from evaluate.aggregate.
supports contains evidence.support outputs. Pass every selected view as
required_views, including ledger for a four-view demonstration.
"""
    required = tuple(required_views)
    if not required or len(set(required)) != len(required):
        raise ValueError('required_views must be nonempty and unique')
    if set(groups) - set(required):
        raise ValueError('Every supplied view must be included in required_views')
    conflicts = [f for f in report['findings'] if f['status'] in CONFLICT_STATUSES]
    unsupported = [s for s in supports if s['unresolved_claims']]
    usable = {
        name: groups[name]['verdict'] for name in required
        if name in groups and groups[name].get('complete') is True
        and groups[name].get('verdict') in ('FLAG', 'NO_FLAG')
    }
    incomplete = [name for name in required if name not in usable]
    reasons = []
    if conflicts:
        reasons.append('EVIDENCE_CONFLICT')
    # Real-world completeness is not estimated by this prototype.
    if report.get('coverage') != 'KNOWN_COMPLETE_SYNTHETIC':
        reasons.append('INCOMPLETE_RECORD')
    if unsupported:
        reasons.append('UNSUPPORTED_CLAIM')
    if len(set(usable.values())) > 1:
        reasons.append('VIEW_FRAGILITY')
    if incomplete:
        reasons.append('MONITOR_ABSTENTION')
    return {
        'action': 'ESCALATE' if reasons else 'ACCEPT',
        'accepted_verdict': None if reasons else next(iter(usable.values())),
        'reason_codes': reasons,
        'event_ids': [e['event_id'] for e in case['events']],
        'receipt_ids': [r['receipt_id'] for r in case['receipts']],
        'details': {
            'required_views': list(required),
            'incomplete_views': incomplete,
            'view_verdicts': usable,
            'evidence_conflicts': conflicts,
            'unsupported_claim_checks': unsupported,
            'coverage': report.get('coverage', 'UNKNOWN'),
            'semantic_support': 'NOT_CHECKED',
        },
    }
